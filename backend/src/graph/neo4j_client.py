import logging
from typing import Any

from neo4j import AsyncGraphDatabase

logger = logging.getLogger(__name__)


class Neo4jClient:
    def __init__(self, uri: str, user: str, password: str):
        self.driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    async def close(self):
        if self.driver:
            await self.driver.close()

    async def ensure_constraints(self):
        """Create uniqueness constraints on critical node IDs."""
        queries = [
            "CREATE CONSTRAINT buyer_id IF NOT EXISTS FOR (b:Buyer) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT seller_id IF NOT EXISTS FOR (s:Seller) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT device_fp IF NOT EXISTS FOR (d:Device) REQUIRE d.fingerprint IS UNIQUE",
            "CREATE CONSTRAINT address_hash IF NOT EXISTS FOR (a:Address) REQUIRE a.hash IS UNIQUE",
            "CREATE CONSTRAINT payment_token IF NOT EXISTS FOR (p:PaymentInstrument) REQUIRE p.token IS UNIQUE",
        ]
        async with self.driver.session() as session:
            for query in queries:
                try:
                    await session.run(query)
                except Exception as e:
                    logger.warning(f"Failed to create constraint: {e}")

    async def ensure_indexes(self):
        """Create indexes on tenant_id for all node types."""
        queries = [
            "CREATE INDEX buyer_tenant IF NOT EXISTS FOR (b:Buyer) ON (b.tenant_id)",
            "CREATE INDEX seller_tenant IF NOT EXISTS FOR (s:Seller) ON (s.tenant_id)",
        ]
        async with self.driver.session() as session:
            for query in queries:
                try:
                    await session.run(query)
                except Exception as e:
                    logger.warning(f"Failed to create index: {e}")

    async def batch_merge_nodes(self, label: str, id_field: str, nodes: list[dict[str, Any]]):
        """Batch merge nodes of a specific label."""
        query = f"""
        UNWIND $nodes AS node
        MERGE (n:{label} {{{id_field}: node.{id_field}}})
        SET n += node
        """
        async with self.driver.session() as session:
            await session.run(query, nodes=nodes)

    async def batch_merge_edges(
        self,
        rel_type: str,
        source_label: str,
        source_id_field: str,
        target_label: str,
        target_id_field: str,
        edges: list[dict[str, Any]],
    ):
        """Batch merge edges between nodes."""
        query = f"""
        UNWIND $edges AS edge
        MATCH (source:{source_label} {{{source_id_field}: edge.source_id}})
        MATCH (target:{target_label} {{{target_id_field}: edge.target_id}})
        MERGE (source)-[r:{rel_type}]->(target)
        SET r += edge.properties
        """
        async with self.driver.session() as session:
            await session.run(query, edges=edges)

    async def get_subgraph(self, node_id: str, depth: int = 2) -> dict:
        """Return ego-network for visualization."""
        query = f"""
        MATCH path = (n {{id: $node_id}})-[*1..{depth}]-(m)
        RETURN path
        """
        nodes = {}
        edges = []
        async with self.driver.session() as session:
            result = await session.run(query, node_id=node_id)
            records = await result.data()
            for record in records:
                path = record.get("path")
                if not path:
                    continue
                # path is a list of nodes and relationships in neo4j python driver?
                # Actually, await result.data() returns dictionaries, but for path it might be complex.
                # Let's extract nodes and relationships manually.
                # It's better to return nodes and relationships directly from the query.

        # Simpler query to extract nodes and rels directly for JSON serialization
        query_direct = f"""
        MATCH path = (n {{id: $node_id}})-[*1..{depth}]-(m)
        UNWIND nodes(path) AS node
        UNWIND relationships(path) AS rel
        RETURN collect(DISTINCT node) AS nodes, collect(DISTINCT rel) AS rels
        """
        async with self.driver.session() as session:
            result = await session.run(query_direct, node_id=node_id)
            single_record = await result.single()
            if not single_record:
                return {"nodes": [], "edges": []}

            for node in single_record["nodes"]:
                nodes[node.element_id] = {
                    "id": node.element_id,
                    "labels": list(node.labels),
                    "properties": dict(node),
                }
            for rel in single_record["rels"]:
                edges.append(
                    {
                        "id": rel.element_id,
                        "source": rel.start_node.element_id,
                        "target": rel.end_node.element_id,
                        "type": rel.type,
                        "properties": dict(rel),
                    }
                )

        return {"nodes": list(nodes.values()), "edges": edges}

    async def health_check(self) -> bool:
        """Check if Neo4j is available."""
        try:
            async with self.driver.session() as session:
                await session.run("RETURN 1")
            return True
        except Exception as e:
            logger.error(f"Neo4j health check failed: {e}")
            return False
