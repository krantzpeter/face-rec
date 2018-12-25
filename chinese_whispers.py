"""
For facenet models, you can use facenet to embedding faces, but what if you want to cluster faces and you don't know how many people? This situation can be applied to:
1 There are a bunch of faces in the monitor to find similar faces.
2 For the face recognition data set, clean the data set
Most existing clustering methods need to know that there are several categories, and then clustering, typically as k means, but if you don't know there are several categories, you need the algorithm to automatically find the number of categories and perform rapid clustering. Is there such a good way?
Have! The answer is Chinese whispers. This method is based on graphs, and one node in the graph corresponds to a human face. The edge between nodes corresponds to the similarity of two nodes, that is, the similarity between two faces, and iteratively finds a node. Corresponding similar weights are summed to find categories and clustered. The features obtained by facenet embedding are used to cluster the ms-celeb data set. After testing, when the model and threshold are selected properly, only 10 iterations can be compared. Good results.

The result of the algorithm mainly depends on the effect of the model and the choice of threshold. When iterating, the similarity is taken as the weight.

https://github.com/zhly0/facenet-face-cluster-chinese-whispers-

Recommended for use:

https://github.com/davidsandberg/facenet/issues/370
"""

""" Face Cluster """
import math
# import tensorflow as tf
# import facenet
import os


def face_distance(face_encodings, face_to_compare):
    """
    Given a list of face encodings, compare them to a known face encoding and get a euclidean distance
    for each comparison face. The distance tells you how similar the faces are.
    :param faces: List of face encodings to compare
    :param face_to_compare: A face encoding to compare against
    :return: A numpy ndarray with the distance for each face in the same order as the 'faces' array
    """
    import numpy as np
    if len(face_encodings) == 0:
        return np.empty((0))
    #return np.sum(face_encodings*face_to_compare,axis=1)
    return 1/np.linalg.norm(face_encodings - face_to_compare, axis=1)

def _chinese_whispers(encoding_list, threshold=0.75, iterations=20):
    """ Chinese Whispers Algorithm

    Modified from Alex Loveless' implementation,
    http://alexloveless.co.uk/data/chinese-whispers-graph-clustering-in-python/

    Inputs:
        encoding_list: a list of facial encodings from face_recognition
        threshold: facial match threshold,default 0.6
        iterations: since chinese whispers is an iterative algorithm, number of times to iterate

    Outputs:
        sorted_clusters: a list of clusters, a cluster being a list of imagepaths,
            sorted by largest cluster to smallest
    """

    #from face_recognition.api import _face_distance
    from random import shuffle
    import networkx as nx
    # Create graph
    nodes = []
    edges = []

    image_paths, encodings = zip(*encoding_list)

    if len(encodings) <= 1:
        print ("No enough encodings to cluster!")
        return []

    for idx, face_encoding_to_check in enumerate(encodings):
        # Adding node of facial encoding
        node_id = idx+1

        # Initialize 'cluster' to unique value (cluster of itself)
        node = (node_id, {'cluster': image_paths[idx], 'path': image_paths[idx]})
        nodes.append(node)

        # Facial encodings to compare
        if (idx+1) >= len(encodings):
            # Node is last element, don't create edge
            break

        compare_encodings = encodings[idx+1:]
        distances = face_distance(compare_encodings, face_encoding_to_check)
        encoding_edges = []
        for i, distance in enumerate(distances):
            if distance > threshold:
                # Add edge if facial match
                edge_id = idx+i+2
                encoding_edges.append((node_id, edge_id, {'weight': distance}))

        edges = edges + encoding_edges

    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)

    # Iterate
    for _ in range(0, iterations):
        cluster_nodes = G.nodes()
        shuffle(cluster_nodes)
        for node in cluster_nodes:
            neighbors = G[node]
            clusters = {}

            for ne in neighbors:
                if isinstance(ne, int):
                    if G.node[ne]['cluster'] in clusters:
                        #The weight of the category of the neighbor node of the node
                        #Corresponding to the dictionary above, meaning
                        #The weight of the file corresponding to a certain path
                        clusters[G.node[ne]['cluster']] += G[node][ne]['weight']
                    else:
                        clusters[G.node[ne]['cluster']] = G[node][ne]['weight']

            # find the class with the highest edge weight sum
            edge_weight_sum = 0
            max_cluster = 0
            #Give the file path corresponding to the maximum weight of the neighbor node to the current node
            for cluster in clusters:
                if clusters[cluster] > edge_weight_sum:
                    edge_weight_sum = clusters[cluster]
                    max_cluster = cluster

            # set the class of target node to the winning local class
            G.node[node]['cluster'] = max_cluster

    clusters = {}

    # Prepare cluster output
    for (_, data) in G.node.items():
        cluster = data['cluster']
        path = data['path']

        if cluster:
            if cluster not in clusters:
                clusters[cluster] = []
            clusters[cluster].append(path)

    # Sort cluster output
    sorted_clusters = sorted(clusters.values(), key=len, reverse=True)

    return sorted_clusters

def cluster_facial_encodings(facial_encodings):
    """ Cluster facial encodings

        Intended to be an optional switch for different clustering algorithms, as of right now
        only chinese whispers is available.

        Input:
            facial_encodings: (image_path, facial_encoding) dictionary of facial encodings

        Output:
            sorted_clusters: a list of clusters, a cluster being a list of imagepaths,
                sorted by largest cluster to smallest

    """

    if len(facial_encodings) <= 1:
        print ("Number of facial encodings must be greater than one, can't cluster")
        return []

    # Only use the chinese whispers algorithm for now
    sorted_clusters = _chinese_whispers(facial_encodings.items())
    return sorted_clusters

def compute_facial_encodings(sess,images_placeholder,embeddings,phase_train_placeholder,image_size,
                	embedding_size,nrof_images,nrof_batches,emb_array,batch_size,paths):
    """ Compute Facial Encodings

        Given a set of images, compute the facial encodings of each face detected in the images and
        return them. If no faces, or more than one face found, return nothing for that image.

        Inputs:
            image_paths: a list of image paths

        Outputs:
            facial_encodings: (image_path, facial_encoding) dictionary of facial encodings

    """

    for i in range(nrof_batches):
        start_index = i*batch_size
        end_index = min((i+1)*batch_size, nrof_images)
        paths_batch = paths[start_index:end_index]
        images = facenet.load_data(paths_batch, False, False, image_size)
        feed_dict = { images_placeholder:images, phase_train_placeholder:False }
        emb_array[start_index:end_index,:] = sess.run(embeddings, feed_dict=feed_dict)

    facial_encodings = {}
    for x in range(nrof_images):
        facial_encodings[paths[x]] = emb_array[x,:]


    return facial_encodings

def main(args):
    """ Main

    Given a list of images, save out facial encoding data files and copy
    images into folders of face clusters.

    """
    from os.path import join, basename, exists
    from os import makedirs
    import numpy as np
    import shutil

    if not exists(args.output):
        makedirs(args.output)

    with tf.Graph().as_default():
        with tf.Session() as sess:
            train_set = facenet.get_dataset(args.input)
            #image_list, label_list = facenet.get_image_paths_and_labels(train_set)

            meta_file, ckpt_file = facenet.get_model_filenames(os.path.expanduser(args.model_dir))

            print('Metagraph file: %s' % meta_file)
            print('Checkpoint file: %s' % ckpt_file)
            facenet.load_model(args.model_dir, meta_file, ckpt_file)

            # Get input and output tensors
            images_placeholder = tf.get_default_graph().get_tensor_by_name("input:0")
            embeddings = tf.get_default_graph().get_tensor_by_name("embeddings:0")
            phase_train_placeholder = tf.get_default_graph().get_tensor_by_name("phase_train:0")

            image_size = images_placeholder.get_shape()[1]
            embedding_size = embeddings.get_shape()[1]

            # Run forward pass to calculate embeddings
            print('Runnning forward pass on images')


            #counter  = 0
            for x in range(len(train_set)):
                #counter += 1
                #if counter<56700:
                #	continue
                if counter % 100 == 0:
                    print(counter)
                image_paths = train_set[x].image_paths
                nrof_images = len(image_paths)
                nrof_batches = int(math.ceil(1.0*nrof_images / args.batch_size))
                emb_array = np.zeros((nrof_images, embedding_size))
                facial_encodings = compute_facial_encodings(sess,images_placeholder,embeddings,phase_train_placeholder,image_size,
                	embedding_size,nrof_images,nrof_batches,emb_array,args.batch_size,image_paths)
                sorted_clusters = cluster_facial_encodings(facial_encodings)
                num_cluster = len(sorted_clusters)
                #print('created %d cluster!',num_cluster)
                #for idx,cluster in enumerate(sorted_clusters):
                #    print('%d th cluster num :%d',idx,len(cluster))
                dest_dir = join(args.output, train_set[x].name)
                # Copy image files to cluster folders
                for idx, cluster in enumerate(sorted_clusters):
                    #This is to save all categories after clustering
                    #cluster_dir = join(dest_dir, str(idx))
                    #Only save the most number of clusters
                    cluster_dir = dest_dir
                    if len(cluster)<5:
                    	break
                    if not exists(cluster_dir):
                        makedirs(cluster_dir)
                    for path in cluster:
                        shutil.copy(path, join(cluster_dir, basename(path)))
                    break


def parse_args():
    """Parse input arguments."""
    import argparse
    parser = argparse.ArgumentParser(description='Get a shape mesh (t-pose)')
    parser.add_argument('--model_dir', type=str, help='model dir', required=True)
    parser.add_argument('--batch_size', type=int, help='model dir', required=30)
    parser.add_argument('--input', type=str, help='Input dir of images', required=True)
    parser.add_argument('--output', type=str, help='Output dir of clusters', required=True)
    args = parser.parse_args()

    return args

if __name__ == '__main__':
    """ Entry point """
    main(parse_args())
