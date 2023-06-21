import os
import pickle
from typing import Union

import faiss
import numpy as np
from sklearn.cluster import DBSCAN, KMeans, estimate_bandwidth, MeanShift

from panoptic.compute.utils import load_similarity_tree, SimilarityTreeWithLabel, SimilarityFaissWithLabel
from panoptic.models import ComputedValue

SIMILARITY_TREE: SimilarityTreeWithLabel = load_similarity_tree()


def create_similarity_tree(images: list[ComputedValue]):
    tree = SimilarityTreeWithLabel(images)
    with open(os.path.join(os.getenv('PANOPTIC_DATA'), 'tree.pkl'), 'wb') as f:
        pickle.dump(tree, f)
    global SIMILARITY_TREE
    SIMILARITY_TREE = tree


def create_similarity_tree_faiss(images: list[ComputedValue]):
    tree = SimilarityFaissWithLabel(images)
    with open(os.path.join(os.getenv('PANOPTIC_DATA'), 'tree_faiss.pkl'), 'wb') as f:
        pickle.dump(tree, f)
    global SIMILARITY_TREE
    SIMILARITY_TREE = tree


def get_similar_images(vectors: list[np.ndarray]):
    if not SIMILARITY_TREE:
        raise ValueError("Cannot compute image similarity since KDTree was not computed yet")
    vector = np.mean(vectors, axis=0)
    return SIMILARITY_TREE.query(vector)


def make_clusters(images: list[ComputedValue], *, method='kmeans', **kwargs) -> (list[list[str]], list[int]):
    res_clusters = []
    res_distances = []
    vectors, sha1, ahashs = zip(*[(i.vector, i.sha1, i.ahash) for i in images])
    sha1 = np.asarray(sha1)
    ahashs = np.asarray(ahashs)
    clusters: np.ndarray
    distances: np.ndarray | None = None
    method = "faiss"
    match method:
        case 'kmeans':
            clusters = _make_clusters_kmeans(vectors, **kwargs)
        case 'dbscan':
            clusters = _make_clusters_dbscan(vectors, **kwargs)
        case 'meanshift':
            clusters = _make_clusters_meanshift(vectors, **kwargs)
        case 'faiss':
            clusters, distances = _make_clusters_faiss(vectors, **kwargs)
        case other:
            return [[]]
    for cluster in list(set(clusters)):
        sha1_clusters = sha1[clusters == cluster]
        ahashs_clusters = ahashs[clusters == cluster]
        # sort by average_hash
        # sorted_cluster = [sha1 for _, sha1 in sorted(zip(ahashs_clusters, sha1_clusters))]
        if distances is not None:
            res_distances.append(np.mean(distances[clusters == cluster]))
        res_clusters.append(list(sha1_clusters))
    # sort clusters by distances
    # TODO: trouver un meilleur indicateur que juste la moyenne des distances ?
    # TODO: virer les groupes avec une seule image ?
    sorted_clusters = [cluster for _, cluster in sorted(zip(res_distances, res_clusters))]
    return sorted_clusters, sorted(res_distances)


def _make_clusters_dbscan(vectors, eps=3, *args, **kwargs) -> np.ndarray:
    clusters = DBSCAN(eps=eps).fit(np.asarray(vectors))
    return clusters.labels_


def _make_clusters_kmeans(vectors, nb_clusters=6, *args, **kwargs) -> np.ndarray:
    clusters = KMeans(n_clusters=int(nb_clusters)).fit_predict(vectors)
    return clusters


def _make_clusters_faiss(vectors, nb_clusters=6, *args, **kwargs) -> (np.ndarray, np.ndarray):
    vectors = np.asarray(vectors)
    kmean = faiss.Kmeans(vectors.shape[1], nb_clusters, niter=20, verbose=False)
    kmean.train(vectors)
    distances, indices = kmean.index.search(vectors, 1)
    return np.asarray([item for sublist in indices for item in sublist]), np.asarray([item for sublist in distances for item in sublist])


def _make_clusters_meanshift(vectors, *args, **kwargs) -> np.ndarray:
    bandwidth = estimate_bandwidth(vectors, quantile=0.2, n_samples=500)
    clusters = MeanShift(bandwidth=bandwidth, bin_seeding=True).fit(np.asarray(vectors))
    return clusters.labels_