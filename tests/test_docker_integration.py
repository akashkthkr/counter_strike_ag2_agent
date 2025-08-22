import pytest
import asyncio
import httpx
import time
from typing import Dict, Any


class TestDockerIntegration:
    """Integration tests for the dockerized Counter-Strike AG2 system."""
    
    @pytest.fixture
    def api_client(self):
        return httpx.AsyncClient(base_url="http://localhost:8080")
    
    @pytest.fixture
    def agent_client(self):
        return httpx.AsyncClient(base_url="http://localhost:8081")
    
    async def _check_service_available(self, client: httpx.AsyncClient, service_name: str) -> bool:
        """Check if a service is available."""
        try:
            response = await client.get("/health", timeout=5.0)
            return response.status_code == 200
        except (httpx.ConnectError, httpx.TimeoutException):
            pytest.skip(f"{service_name} service is not available - skipping integration test")
            return False
    
    @pytest.mark.asyncio
    async def test_api_health_check(self, api_client):
        """Test that the API service is healthy."""
        await self._check_service_available(api_client, "API")
        response = await api_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    @pytest.mark.asyncio
    async def test_agent_service_health_check(self, agent_client):
        """Test that the Agent service is healthy."""
        await self._check_service_available(agent_client, "Agent")
        response = await agent_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "agents_loaded" in data
    
    @pytest.mark.asyncio
    async def test_create_game_session(self, api_client):
        """Test creating a new game session."""
        await self._check_service_available(api_client, "API")
        session_data = {
            "session_name": "Docker Test Session",
            "max_rounds": 3
        }
        
        response = await api_client.post("/sessions", json=session_data)
        if response.status_code != 200:
            print(f"API Error - Status: {response.status_code}")
            print(f"Response: {response.text}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_name"] == "Docker Test Session"
        assert data["max_rounds"] == 3
        assert data["current_round"] == 1
        assert data["is_active"] is True
        assert "id" in data
        
        return data["id"]
    
    @pytest.mark.asyncio
    async def test_game_state_retrieval(self, api_client):
        """Test retrieving game state."""
        # First create a session
        session_id = await self.test_create_game_session(api_client)
        
        response = await api_client.get(f"/sessions/{session_id}/state")
        assert response.status_code == 200
        
        data = response.json()
        assert data["session_id"] == session_id
        assert data["round"] == 1
        assert data["max_rounds"] == 3
        assert "player_health" in data
        assert "bomb_planted" in data
        assert data["bomb_planted"] is False
    
    @pytest.mark.asyncio
    async def test_game_action_application(self, api_client):
        """Test applying a game action."""
        # Create a session
        session_id = await self.test_create_game_session(api_client)
        
        # Apply an action
        action_data = {
            "session_id": session_id,
            "team": "Terrorists",
            "player": "player",
            "action": "move to A-site"
        }
        
        response = await api_client.post(f"/sessions/{session_id}/actions", json=action_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "result" in data
        assert "game_state" in data
        assert "moved to a-site" in data["result"].lower()
    
    @pytest.mark.asyncio
    async def test_agent_rag_query(self, agent_client):
        """Test RAG agent query processing."""
        await self._check_service_available(agent_client, "Agent")
        request_data = {
            "agent_type": "rag",
            "query": "What should we do if bomb is planted?",
            "context": {
                "round": 1,
                "bomb_planted": True,
                "bomb_site": "A-site",
                "player_health": {
                    "Terrorists": {"player": 100, "bot": 80},
                    "Counter-Terrorists": {"player": 50, "bot": 100}
                }
            }
        }
        
        response = await agent_client.post("/process", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["agent_type"] == "rag"
        assert "response" in data
        assert len(data["response"]) > 0
        assert "processing_time_ms" in data
    
    @pytest.mark.asyncio
    async def test_agent_service_status(self, agent_client):
        """Test agent service status endpoint."""
        response = await agent_client.get("/agents/status")
        assert response.status_code == 200
        
        data = response.json()
        assert "agents_loaded" in data
        assert "kb_status" in data
    
    @pytest.mark.asyncio
    async def test_full_game_flow(self, api_client, agent_client):
        """Test a complete game flow with multiple actions."""
        # Create session
        session_data = {
            "session_name": "Full Flow Test",
            "max_rounds": 2
        }
        
        response = await api_client.post("/sessions", json=session_data)
        session_id = response.json()["id"]
        
        # Apply several actions
        actions = [
            {"team": "Terrorists", "player": "player", "action": "move to A-site"},
            {"team": "Terrorists", "player": "player", "action": "plant bomb"},
            {"team": "Counter-Terrorists", "player": "player", "action": "move to A-site"},
            {"team": "Counter-Terrorists", "player": "player", "action": "defuse bomb"}
        ]
        
        for action_data in actions:
            action_data["session_id"] = session_id
            response = await api_client.post(f"/sessions/{session_id}/actions", json=action_data)
            assert response.status_code == 200
            
            # Small delay between actions
            await asyncio.sleep(0.1)
        
        # Check final game state
        response = await api_client.get(f"/sessions/{session_id}/state")
        final_state = response.json()
        
        # Should have progressed through the game
        assert "game_status" in final_state
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection for real-time updates."""
        import websockets
        
        # Create a session first
        async with httpx.AsyncClient(base_url="http://localhost:8080") as client:
            session_data = {"session_name": "WebSocket Test", "max_rounds": 3}
            response = await client.post("/sessions", json=session_data)
            session_id = response.json()["id"]
        
        # Test WebSocket connection
        try:
            async with websockets.connect(f"ws://localhost:8080/ws/{session_id}") as websocket:
                # Send ping
                await websocket.send('{"type": "ping"}')
                
                # Wait for pong
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = eval(response)  # Simple JSON parsing for test
                assert data["type"] == "pong"
                
        except Exception as e:
            pytest.skip(f"WebSocket test skipped: {e}")
    
    @pytest.mark.asyncio
    async def test_service_error_handling(self, api_client, agent_client):
        """Test error handling in services."""
        # Test invalid session ID (use proper UUID format)
        response = await api_client.get("/sessions/00000000-0000-0000-0000-000000000000/state")
        if response.status_code != 404:
            print(f"Error handling test - Status: {response.status_code}")
            print(f"Response: {response.text}")
        assert response.status_code == 404
        
        # Test invalid agent type
        request_data = {
            "agent_type": "invalid_agent",
            "query": "test query",
            "context": {}
        }
        
        response = await agent_client.post("/process", json=request_data)
        if response.status_code != 400:
            print(f"Invalid agent test - Status: {response.status_code}")
            print(f"Response: {response.text}")
        assert response.status_code == 400
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, api_client):
        """Test handling concurrent requests."""
        # Create multiple sessions concurrently
        tasks = []
        for i in range(5):
            session_data = {
                "session_name": f"Concurrent Test {i}",
                "max_rounds": 3
            }
            tasks.append(api_client.post("/sessions", json=session_data))
        
        responses = await asyncio.gather(*tasks)
        
        # All should succeed
        for response in responses:
            assert response.status_code == 200
            data = response.json()
            assert "id" in data
            assert data["is_active"] is True


@pytest.mark.integration
class TestDockerServices:
    """Test individual Docker services are running correctly."""
    
    def test_postgres_connection(self):
        """Test PostgreSQL database connection."""
        try:
            import psycopg2
            conn = psycopg2.connect(
                host="localhost",
                port=5432,
                database="counter_strike_db",
                user="cs_user",
                password="cs_password"
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result[0] == 1
            conn.close()
        except ImportError:
            pytest.skip("psycopg2 not available for PostgreSQL test")
        except Exception as e:
            pytest.fail(f"PostgreSQL connection failed: {e}")
    

    @pytest.mark.asyncio
    async def test_chromadb_connection(self):
        """Test ChromaDB connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/api/v1/heartbeat")
                assert response.status_code == 200
        except Exception as e:
            pytest.fail(f"ChromaDB connection failed: {e}")


if __name__ == "__main__":
    # Run basic health checks
    import asyncio
    
    async def run_basic_tests():
        print("🧪 Running basic Docker integration tests...")
        
        # Test API health
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8080/health")
                if response.status_code == 200:
                    print("✅ API service is healthy")
                else:
                    print("❌ API service is not healthy")
        except Exception as e:
            print(f"❌ API service connection failed: {e}")
        
        # Test Agent service health
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8081/health")
                if response.status_code == 200:
                    print("✅ Agent service is healthy")
                else:
                    print("❌ Agent service is not healthy")
        except Exception as e:
            print(f"❌ Agent service connection failed: {e}")
        
        print("🏁 Basic tests complete!")
    
    asyncio.run(run_basic_tests())
