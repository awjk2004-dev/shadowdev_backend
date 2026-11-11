import unittest

from app.models.player import Player, sync_player_progress


class SkillPointProgressionTests(unittest.TestCase):
    def test_level_up_awards_one_skill_point(self):
        player = Player(xp=100, level=1, rank="E", skill_points=10)

        sync_player_progress(player)

        self.assertEqual(player.level, 2)
        self.assertEqual(player.skill_points, 11)

    def test_repeated_progress_sync_does_not_award_twice(self):
        player = Player(xp=400, level=2, rank="E", skill_points=11)

        sync_player_progress(player)
        sync_player_progress(player)

        self.assertEqual(player.level, 3)
        self.assertEqual(player.skill_points, 12)

    def test_multiple_levels_award_one_point_per_level(self):
        player = Player(xp=900, level=1, rank="E", skill_points=10)

        sync_player_progress(player)

        self.assertEqual(player.level, 4)
        self.assertEqual(player.skill_points, 13)
