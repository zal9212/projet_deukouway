from locust import HttpUser, task, between, SequentialTaskSet

class DekouwayUserBehavior(SequentialTaskSet):

    @task(3)
    def load_homepage(self):
        self.client.get("/", name="Homepage")

    @task(2)
    def search_properties(self):
        self.client.get("/api/v1/properties/?city=Dakar", name="API Search Properties")

    @task(1)
    def get_featured_properties(self):
        self.client.get("/api/v1/properties/featured/", name="API Featured Properties")

    @task(1)
    def ask_chatbot_groq(self):
        self.client.post("/api/v1/ai/recommendations/", json={
            "city": "Dakar",
            "max_price": "150000.00"
        }, name="API AI Recommendation")


class DekouwayLoadTest(HttpUser):
    tasks = [DekouwayUserBehavior]
    wait_time = between(1, 3)
