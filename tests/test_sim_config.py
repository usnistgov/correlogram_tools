import os
from correlogram_tools import sim_config
from correlogram_tools.sim_config import SimConfig
import unittest
from pathlib import Path


class TestSimConfig(unittest.TestCase):

    def setUp(self):
        self.test_config = {
            "title": "Test Title",
            "description": "Test description.",
            "mask_path": "../roi_mask.tif",
            "thickness_path": "../thickness_mask.tif",
        }
        self.test_dictionary = {
            "keyword": [
                100,
                {
                    "keyword": 1,
                    "not_keyword": 200,
                    "not_a_keyword": {"keyword": 2},
                },
                {
                    "not_keyword": 300,
                },
                400,
            ],
            "not_keyword": [
                500,
                600,
                {"keyword": 3}
            ],
            "another_not_keyword": {"not_keyword": 700, "keyword": [4, 5, 6]},
            "last_not_keyword": {"keyword": {"not_a_keyword": 800}}
        }
        self.config_path = os.path.abspath("test_data/test_config.json")
        self.sim_config = SimConfig(config_dict=self.test_config, config_path=self.config_path)

    def test_dictionary_search(self):
        true_answer = [
            [
                100,
                {"keyword": 1, "not_keyword": 200, "not_a_keyword": {"keyword": 2}},
                {"not_keyword": 300},
                400
            ],
            1, 2, 3, [4, 5, 6], {"not_a_keyword": 800},
        ]
        check_answer = list(sim_config.deep_key(self.test_dictionary, target="keyword"))
        self.assertListEqual(true_answer, check_answer)

    def test_config_search(self):
        true_answer = [self.test_config["description"]]
        check_answer = list(self.sim_config.__getitem__("description"))
        self.assertListEqual(true_answer, check_answer)

    def test_title(self):
        true_answer = self.test_config["title"]
        check_answer = self.sim_config.title
        self.assertEqual(true_answer, check_answer)

    def test_description(self):
        true_answer = self.test_config["description"]
        check_answer = self.sim_config.description
        self.assertEqual(true_answer, check_answer)

    def test_mask_path(self):
        true_answer = os.path.join(os.path.dirname(self.config_path), os.path.relpath(self.test_config["mask_path"]))
        check_answer = str(self.sim_config.mask_path)
        self.assertEqual(true_answer, check_answer)

    def test_thickness_path(self):
        true_answer = os.path.join(os.path.dirname(self.config_path),
                                   os.path.relpath(self.test_config["thickness_path"]))
        check_answer = str(self.sim_config.thickness_path)
        self.assertEqual(true_answer, check_answer)

    def test_config_attribute(self):
        self.assertEqual(self.test_config, self.sim_config.config)

    def test_config_path_attribute(self):
        self.assertEqual(Path(self.config_path).expanduser().absolute(), self.sim_config.config_path)


if __name__ == "__main__":
    unittest.main()