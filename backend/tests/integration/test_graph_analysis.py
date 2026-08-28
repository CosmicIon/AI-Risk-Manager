import asyncio
import sys
import uuid

import pytest

from src.config import settings
from src.core.enums import AlertSeverity
from src.graph.community_detection import detect_suspicious_communities, run_louvain
from src.graph.neo4j_client import Neo4jClient
from src.graph.ring_scorer import format_for_alert, generate_ring_narrative, score_ring

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture
async def neo4j_client():
    password = (
        settings.NEO4J_PASSWORD.get_secret_value()
        if hasattr(settings.NEO4J_PASSWORD, "get_secret_value")
        else settings.NEO4J_PASSWORD
    )
    client = Neo4jClient(uri=settings.NEO4J_URI, user=settings.NEO4J_USER, password=password)
    yield client
    await client.close()


@pytest.fixture(autouse=True)
async def clear_neo4j(neo4j_client):
    async with neo4j_client.driver.session() as session:
        await session.run("MATCH (n) DETACH DELETE n")
        try:
            await session.run("CALL gds.graph.drop('test_graph', false)")
        except Exception:
            pass


@pytest.mark.asyncio
async def test_batch_node_creation(neo4j_client):
    nodes = [
        {"id": "b1", "tenant_id": "t1", "name": "Buyer 1"},
        {"id": "b2", "tenant_id": "t1", "name": "Buyer 2"},
    ]
    await neo4j_client.batch_merge_nodes("Buyer", "id", nodes)

    async with neo4j_client.driver.session() as session:
        result = await session.run("MATCH (b:Buyer) RETURN count(b) as count")
        record = await result.single()
        assert record["count"] == 2


@pytest.mark.asyncio
async def test_louvain_detects_planted_ring(neo4j_client):
    tenant_id = uuid.uuid4()
    # Plant a ring: 3 buyers, 1 device, 1 address, buying from 1 seller
    buyers = [
        {"id": "b1", "tenant_id": str(tenant_id)},
        {"id": "b2", "tenant_id": str(tenant_id)},
        {"id": "b3", "tenant_id": str(tenant_id)},
    ]
    device = [{"fingerprint": "d1", "tenant_id": str(tenant_id)}]
    address = [{"hash": "a1", "tenant_id": str(tenant_id)}]
    seller = [{"id": "s1", "tenant_id": str(tenant_id)}]
    payment = [{"token": "p1", "tenant_id": str(tenant_id)}]

    await neo4j_client.batch_merge_nodes("Buyer", "id", buyers)
    await neo4j_client.batch_merge_nodes("Device", "fingerprint", device)
    await neo4j_client.batch_merge_nodes("Address", "hash", address)
    await neo4j_client.batch_merge_nodes("Seller", "id", seller)
    await neo4j_client.batch_merge_nodes("PaymentInstrument", "token", payment)

    # Create edges
    edges_uses = [
        {"source_id": "b1", "target_id": "d1", "properties": {}},
        {"source_id": "b2", "target_id": "d1", "properties": {}},
        {"source_id": "b3", "target_id": "d1", "properties": {}},
    ]
    edges_ships = [
        {"source_id": "b1", "target_id": "a1", "properties": {}},
        {"source_id": "b2", "target_id": "a1", "properties": {}},
        {"source_id": "b3", "target_id": "a1", "properties": {}},
    ]
    edges_bought = [
        {"source_id": "b1", "target_id": "s1", "properties": {}},
        {"source_id": "b2", "target_id": "s1", "properties": {}},
        {"source_id": "b3", "target_id": "s1", "properties": {}},
    ]
    edges_pays = [
        {"source_id": "b1", "target_id": "p1", "properties": {}},
    ]

    await neo4j_client.batch_merge_edges("USES", "Buyer", "id", "Device", "fingerprint", edges_uses)
    await neo4j_client.batch_merge_edges("SHIPS_TO", "Buyer", "id", "Address", "hash", edges_ships)
    await neo4j_client.batch_merge_edges("BOUGHT_FROM", "Buyer", "id", "Seller", "id", edges_bought)
    await neo4j_client.batch_merge_edges(
        "PAYS_WITH", "Buyer", "id", "PaymentInstrument", "token", edges_pays
    )

    communities = await run_louvain(neo4j_client, tenant_id, min_community_size=3)
    assert len(communities) > 0

    suspicious = await detect_suspicious_communities(neo4j_client, tenant_id, communities)
    assert len(suspicious) > 0

    community = suspicious[0]
    assert community["buyers"] == 3
    assert community["devices"] == 1
    assert community["addresses"] == 1


def test_ring_scorer_flags_suspicious_cluster():
    community = {"buyers": 5, "devices": 1, "addresses": 2, "community_id": 123}
    stats = {"timing_score": 0.8, "chargeback_rate": 0.1}

    score = score_ring(community, stats)
    assert score > 0.7

    narrative = generate_ring_narrative(community, score)
    assert "High Suspicion Ring" in narrative
    assert "5 distinct buyers" in narrative

    alert = format_for_alert(community, score, narrative, uuid.uuid4())
    assert alert is not None
    assert alert.severity in [AlertSeverity.WARNING, AlertSeverity.CRITICAL]


@pytest.mark.asyncio
async def test_subgraph_extraction(neo4j_client):
    nodes = [{"id": "b1", "tenant_id": "t1"}]
    await neo4j_client.batch_merge_nodes("Buyer", "id", nodes)
    device = [{"fingerprint": "d1", "tenant_id": "t1"}]
    await neo4j_client.batch_merge_nodes("Device", "fingerprint", device)

    edges = [{"source_id": "b1", "target_id": "d1", "properties": {}}]
    await neo4j_client.batch_merge_edges("USES", "Buyer", "id", "Device", "fingerprint", edges)

    subgraph = await neo4j_client.get_subgraph("b1", depth=1)

    assert len(subgraph["nodes"]) == 2
    assert len(subgraph["edges"]) == 1
