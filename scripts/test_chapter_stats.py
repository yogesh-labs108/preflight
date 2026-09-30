import unittest

from chapter_stats import capitalised_mid_sentence, draft_episodes


def chapter(number, minutes):
    return {"number": number, "minutes": minutes}


class NamesTest(unittest.TestCase):
    def test_finds_names_and_skips_titles_and_sentence_starts(self):
        body = "Steward Hu gave him a robe. Elder Fang sent him to Qiao Lin."
        self.assertEqual(capitalised_mid_sentence(body), ["Hu", "Fang", "Qiao", "Lin"])

    def test_ignores_the_first_word_of_a_line(self):
        self.assertEqual(capitalised_mid_sentence("Nothing happened.\nThen it did."), [])

    def test_ignores_i_and_strips_possessives(self):
        self.assertEqual(capitalised_mid_sentence("So I'll see Li Wen's furnace, and I agree."), ["Li", "Wen"])


class DraftEpisodesTest(unittest.TestCase):
    def test_long_chapter_becomes_its_own_episode(self):
        episodes = draft_episodes([chapter(1, 12), chapter(2, 12)], 12)
        self.assertEqual([[c["number"] for c in group] for group in episodes], [[1], [2]])

    def test_short_chapters_are_merged_up_to_the_target(self):
        episodes = draft_episodes([chapter(n, 4) for n in range(1, 7)], 12)
        self.assertEqual([[c["number"] for c in group] for group in episodes], [[1, 2, 3], [4, 5, 6]])

    def test_never_builds_an_episode_far_past_the_target(self):
        episodes = draft_episodes([chapter(1, 8), chapter(2, 14)], 12)
        self.assertEqual([[c["number"] for c in group] for group in episodes], [[1], [2]])


if __name__ == "__main__":
    unittest.main()
