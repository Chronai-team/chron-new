import pytest
from analyzer.authenticity_detector import AuthenticityDetector
import os
import tempfile
import shutil

@pytest.fixture
def temp_repo():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def authenticity_detector(temp_repo):
    return AuthenticityDetector(temp_repo)

def create_test_file(repo_path: str, content: str, filename: str = "test.py"):
    """Helper to create test files"""
    file_path = os.path.join(repo_path, filename)
    with open(file_path, "w") as f:
        f.write(content)

@pytest.mark.asyncio
async def test_detect_tensorflow(temp_repo, authenticity_detector):
    create_test_file(temp_repo, """
import tensorflow as tf
model = tf.keras.Sequential()
""")
    score = await authenticity_detector.analyze_authenticity()
    assert score > 0

@pytest.mark.asyncio
async def test_detect_pytorch(temp_repo, authenticity_detector):
    create_test_file(temp_repo, """
import torch
import torch.nn as nn
""")
    score = await authenticity_detector.analyze_authenticity()
    assert score > 0

@pytest.mark.asyncio
async def test_detect_no_ai(temp_repo, authenticity_detector):
    create_test_file(temp_repo, """
import json
data = {"test": "data"}
""")
    score = await authenticity_detector.analyze_authenticity()
    assert score == 0

@pytest.mark.asyncio
async def test_detect_multiple_frameworks(temp_repo, authenticity_detector):
    create_test_file(temp_repo, """
import tensorflow as tf
import torch
from transformers import AutoModel
""")
    score = await authenticity_detector.analyze_authenticity()
    assert score > 0.5  # Should detect multiple frameworks
