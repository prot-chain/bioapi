from locust import HttpUser, task, between


class ProteinApiUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def fetch_uniprot_data(self):
        self.client.get("/api/v1/protein/P12345")

    @task
    def fetch_pdb_data(self):
        self.client.get("/api/v1/protein/1HNY")
