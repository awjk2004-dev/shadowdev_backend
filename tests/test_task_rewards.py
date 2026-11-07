from datetime import datetime
import unittest

from pydantic import ValidationError

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskResponse, TaskUpdate


class TaskRewardTests(unittest.TestCase):
    def test_create_defaults_to_easy_reward(self):
        task = TaskCreate(title="Read", dimension="mind")
        model = Task(
            id=1,
            user_id=1,
            title=task.title,
            dimension=task.dimension,
            difficulty=task.difficulty,
        )

        self.assertEqual(model.xp_reward, 10)

    def test_difficulty_maps_to_configured_rewards(self):
        expected_rewards = {"easy": 10, "medium": 25, "hard": 50}

        for difficulty, expected_reward in expected_rewards.items():
            with self.subTest(difficulty=difficulty):
                task = Task(
                    id=1,
                    user_id=1,
                    title="Task",
                    dimension="mind",
                    difficulty=difficulty,
                )
                self.assertEqual(task.xp_reward, expected_reward)

    def test_update_accepts_difficulty_and_does_not_accept_client_reward(self):
        update = TaskUpdate(difficulty="hard")

        self.assertEqual(update.difficulty, "hard")
        with self.assertRaises(ValidationError):
            TaskUpdate(difficulty="hard", xp_reward=1000)

    def test_response_includes_server_calculated_reward(self):
        task = Task(
            id=1,
            user_id=1,
            title="Task",
            dimension="body",
            difficulty="medium",
            is_active=True,
        )
        task.created_at = datetime.now()

        response = TaskResponse.model_validate(task)

        self.assertEqual(response.xp_reward, 25)

    def test_rejects_unknown_difficulty(self):
        with self.assertRaises(ValidationError):
            TaskCreate(title="Task", dimension="mind", difficulty="legendary")


if __name__ == "__main__":
    unittest.main()
