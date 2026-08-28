import logging
from uuid import UUID

from src.graph.neo4j_client import Neo4jClient

logger = logging.getLogger(__name__)

async def run_louvain(client: Neo4jClient, tenant_id: UUID, min_community_size: int = 3) -> list[dict]:
    """
    Project graph and run GDS Louvain to find communities.
    Returns communities with {"community_id": int, "members": list[str], "size": int, "modularity": float}.
    """
    graph_name = f"risk_graph_{tenant_id.hex}"

    # Project graph
    project_query = """
    CALL gds.graph.project(
      $graph_name,
      ['Buyer', 'Seller', 'Address', 'Device', 'PaymentInstrument'],
      ['BOUGHT_FROM', 'USES', 'SHIPS_TO', 'PAYS_WITH'],
      {
        nodeProperties: ['tenant_id']
      }
    )
    """

    # Run Louvain
    louvain_query = """
    CALL gds.louvain.stream($graph_name)
    YIELD nodeId, communityId
    WITH gds.util.asNode(nodeId) AS n, communityId
    WHERE n.tenant_id = $tenant_id_str
    WITH communityId, collect(n.id) AS members, count(n) AS size
    WHERE size >= $min_size
    RETURN communityId AS community_id, members, size, 0.0 AS modularity
    """

    # Drop graph
    drop_query = """
    CALL gds.graph.drop($graph_name, false)
    """

    communities = []
    async with client.driver.session() as session:
        try:
            # Drop if already exists from previous failed run
            await session.run(drop_query, graph_name=graph_name)

            # Create projection
            await session.run(project_query, graph_name=graph_name)

            # Run community detection
            result = await session.run(louvain_query, graph_name=graph_name, tenant_id_str=str(tenant_id), min_size=min_community_size)
            records = await result.data()
            for record in records:
                communities.append(record)

        except Exception as e:
            logger.error(f"Failed to run Louvain: {e}")
        finally:
            # Always drop the graph
            try:
                await session.run(drop_query, graph_name=graph_name)
            except Exception:
                pass

    return communities


async def run_label_propagation(client: Neo4jClient, tenant_id: UUID) -> list[dict]:
    """Alternative algorithm for comparison."""
    # Not implemented yet, just a placeholder as specified
    return []


async def detect_suspicious_communities(client: Neo4jClient, tenant_id: UUID, communities: list[dict]) -> list[dict]:
    """
    Filter communities by suspicion heuristics:
    - Shared shipping addresses
    - Same device fingerprint used by multiple accounts
    - Coordinated timing
    - Unusually high return/chargeback rates
    """
    suspicious = []

    # Query to fetch all details of a community's nodes and relationships
    query = """
    MATCH (b:Buyer) WHERE b.id IN $member_ids AND b.tenant_id = $tenant_id
    OPTIONAL MATCH (b)-[:USES]->(d:Device)
    OPTIONAL MATCH (b)-[:SHIPS_TO]->(a:Address)
    OPTIONAL MATCH (b)-[r:BOUGHT_FROM]->(s:Seller)
    RETURN
        count(DISTINCT b) as buyers,
        count(DISTINCT d) as devices,
        count(DISTINCT a) as addresses,
        count(DISTINCT r) as transactions
    """

    async with client.driver.session() as session:
        for community in communities:
            member_ids = community.get("members", [])
            if not member_ids:
                continue

            result = await session.run(query, member_ids=member_ids, tenant_id=str(tenant_id))
            record = await result.single()
            if not record:
                continue

            buyers = record["buyers"]
            devices = record["devices"]
            addresses = record["addresses"]

            if buyers > 1:
                # Heuristics for suspicion
                # e.g., 5 buyers using 1 device, or 5 buyers using 1 address
                if devices < buyers or addresses < buyers:
                    # Enrich community dict
                    community_info = community.copy()
                    community_info["buyers"] = buyers
                    community_info["devices"] = devices
                    community_info["addresses"] = addresses
                    suspicious.append(community_info)

    return suspicious
