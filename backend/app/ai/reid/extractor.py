import logging
from typing import Any, List, Optional, Tuple, Union
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)

class LightweightFeatureExtractor(nn.Module):
    """512-dimensional embedding extractor for cross-camera visual appearance re-identification."""

    def __init__(self, embedding_dim: int = 512):
        super().__init__()
        # 3-stage convolutional backbone with adaptive pooling
        self.conv1 = nn.Conv2d(3, 64, kernel_size=7, stride=2, padding=3, bias=False)
        self.bn1 = nn.BatchNorm2d(64)
        self.relu = nn.ReLU(inplace=True)
        self.maxpool = nn.MaxPool2d(kernel_size=3, stride=2, padding=1)

        self.layer1 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(128),
            nn.ReLU(inplace=True),
        )
        self.layer2 = nn.Sequential(
            nn.Conv2d(128, 256, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(256),
            nn.ReLU(inplace=True),
        )
        self.layer3 = nn.Sequential(
            nn.Conv2d(256, 512, kernel_size=3, stride=2, padding=1, bias=False),
            nn.BatchNorm2d(512),
            nn.ReLU(inplace=True),
        )
        self.avgpool = nn.AdaptiveAvgPool2d((1, 1))
        self.fc = nn.Linear(512, embedding_dim)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)

        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        feat = self.fc(x)
        # L2 normalize embeddings so cosine similarity is simply dot product
        return F.normalize(feat, p=2, dim=1)


class AppearanceEmbeddingExtractor:
    """Extracts visual appearance vectors from person and vehicle crops."""

    def __init__(self, device: str = "cpu", embedding_dim: int = 512):
        self.device = torch.device("cuda" if device == "cuda" and torch.cuda.is_available() else "cpu")
        self.embedding_dim = embedding_dim
        self.model = LightweightFeatureExtractor(embedding_dim=embedding_dim).to(self.device)
        self.model.eval()

    def extract(self, image_crop: np.ndarray) -> np.ndarray:
        """Extracts 512-dim L2-normalized visual embedding from an image crop (BGR/RGB)."""
        if image_crop is None or image_crop.size == 0:
            return np.zeros(self.embedding_dim, dtype=np.float32)

        try:
            import cv2
            # Resize crop to standard Re-ID dimension: 256 height x 128 width for persons/vehicles
            resized = cv2.resize(image_crop, (128, 256), interpolation=cv2.INTER_LINEAR)
            
            # Normalize to [0, 1] tensor in CHW format
            tensor = torch.from_numpy(resized).permute(2, 0, 1).float() / 255.0
            # Standard ImageNet mean/std normalization
            mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
            std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
            tensor = (tensor - mean) / std
            tensor = tensor.unsqueeze(0).to(self.device)

            with torch.no_grad():
                feat = self.model(tensor)
                embedding = feat.squeeze(0).cpu().numpy()
                return embedding.astype(np.float32)
        except Exception as exc:
            logger.warning(f"Feature extraction fallback: {exc}")
            return np.zeros(self.embedding_dim, dtype=np.float32)

    @staticmethod
    def compute_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Computes cosine similarity between two L2-normalized feature vectors."""
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


_global_reid_extractor: Optional[AppearanceEmbeddingExtractor] = None


def get_global_reid_extractor() -> AppearanceEmbeddingExtractor:
    global _global_reid_extractor
    if _global_reid_extractor is None:
        _global_reid_extractor = AppearanceEmbeddingExtractor()
    return _global_reid_extractor
