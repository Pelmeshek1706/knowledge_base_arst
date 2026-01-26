from __future__ import annotations

from typing import Any, Dict, List, Optional

from neo4j import GraphDatabase, Driver, Session

from graphrag.config import Neo4jConfig


class Neo4jClient:
    """
    Minimal Neo4j client wrapper.

    Uses the official Neo4j Python driver. :contentReference[oaicite:2]{index=2}
    """

    def __init__(self, config: Neo4jConfig):
        self._config = config
        self._driver: Optional[Driver] = None

    def connect(self) -> None:
        self._driver = GraphDatabase.driver(
            self._config.uri,
            auth=(self._config.username, self._config.password),
        )
        # quick sanity check
        with self.session() as s:
            s.run("RETURN 1").consume()

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def session(self) -> Session:
        if self._driver is None:
            raise RuntimeError("Neo4jClient is not connected. Call connect() first.")
        return self._driver.session()

    def run(
        self,
        cypher: str,
        parameters: Optional[Dict[str, Any]] = None,
        *,
        raw: bool = False,
    ) -> List[Any]:
        params = parameters or {}
        with self.session() as session:
            result = session.run(cypher, params)
            if raw:
                return list(result)
            return [record.data() for record in result]

    def execute_write(self, cypher: str, parameters: Optional[Dict[str, Any]] = None) -> None:
        params = parameters or {}

        def _tx(tx):
            tx.run(cypher, params).consume()

        with self.session() as session:
            session.execute_write(_tx)
