from api.config import client


class TaskService:
    def __init__(self):
        self.client = client

    def get_all_tasks(self):
        return self.task_repository.get_all_tasks()

    def create_task(self, task):
        return self.task_repository.create_task(task)

    def get_task_by_id(self, task_id):
        return self.task_repository.get_task_by_id(task_id)

    def update_task(self, task_id, task):
        return self.task_repository.update_task(task_id, task)

    def delete_task(self, task_id):
        return self.task_repository.delete_task(task_id)