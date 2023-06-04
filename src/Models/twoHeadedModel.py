import torch
import torch.nn as nn
from sklearn.cluster import KMeans

class twoHeadedModel(nn.Module):
    def __init__(self, encoder, classifier):
        super(twoHeadedModel, self).__init__()
        self.encoder = encoder
        self.classifier = classifier
        
    def forward(self, x):
        x = self.encoder(x)
        x = self.classifier(x)
        return x


class TwoHeadedLoss(nn.Module):
    def __init__(self, num_clusters, classification_loss_fn):
        super(TwoHeadedLoss, self).__init__()
        self.num_clusters = num_clusters
        self.classification_loss_fn = classification_loss_fn
        self.kmeans = KMeans(n_clusters=num_clusters)

    def forward(self, features, labels, classification_logits):
        # Update cluster centers using k-means
        self.kmeans.fit(features.detach().cpu().numpy())
        cluster_centers = torch.from_numpy(self.kmeans.cluster_centers_).to(features.device)
        
        # Compute cluster loss
        distances = torch.cdist(features, cluster_centers)
        softmax_weights = nn.functional.softmax(-distances, dim=1)
        cluster_loss = torch.mean(
            softmax_weights[:, 0] * distances[:, 0] + (1 - softmax_weights[:, 1]) * distances[:, 1]
        )
        
        # Compute classification loss
        classification_loss = self.classification_loss_fn(classification_logits, labels)
        
        # Combine the two losses
        total_loss = cluster_loss + classification_loss
        
        return total_loss

