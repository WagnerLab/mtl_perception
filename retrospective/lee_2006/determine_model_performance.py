import os, pickle, imp 
import numpy as np
from scipy.misc import imread, imresize
from sklearn import cluster
from PIL import Image
import tensorflow.compat.v1 as tf
import warnings; warnings.simplefilter('ignore')

def get_session():
    """returns tensorflow session"""
    config = tf.ConfigProto(allow_soft_placement = True)
    config.gpu_options.per_process_gpu_memory_fraction = 0.4
    config.gpu_options.allow_growth = True
    return tf.Session(config = config)

def define_model(path_to_model): 
    """returns model"""
    tf.disable_v2_behavior()
    session = get_session()
    vgg16 = imp.load_source('vgg16', os.path.join(path_to_model,  'vgg16.py'))
    imgs = tf.placeholder(tf.float32, [None, 224, 224, 3])
    vgg = vgg16.vgg16(imgs, os.path.join(path_to_model, 'vgg16_weights.npz'), session)
    return vgg, session

def determine_order_of_clusters(clusters, i_image):
    """determine how to map cluster order onto image order """

    # split into halves
    ys = (clusters[:,0] > (i_image.shape[0]/2) )
    xs = (clusters[:,1] > (i_image.shape[1]/2) )

    # manually determine how to map cluster onto image order
    order = []
    order.append( np.nonzero((xs == 0) * (ys == 0))[0][0]) # first
    order.append( np.nonzero((xs == 1) * (ys == 0))[0][0]) # second
    order.append( np.nonzero((xs == 0) * (ys == 1))[0][0]) # third
    order.append( np.nonzero((xs == 1) * (ys == 1))[0][0]) # fourth

    return np.array(order)

def extract_stimuli(stimulus_directory):
    """returns experimental stimuli"""

    # identify all experimental folders
    task_folders = [i for i in os.listdir(stimulus_directory) if '4' in i]
    # manually determined optimal crop for each image, after identifying COMs
    type_info = {'face': (95, 95, 'faces') ,'scene': (150, 225, 'scenes')}
    # initialize data structures
    experimental_stimuli, answer_key = {}, {}

    for i_folder in  [i for i in task_folders]:
        
        # determine optimize crop parameters 
        if 'face' in i_folder:
            w, h, i_type = type_info['face']
        else:
            w, h, i_type = type_info['scene']
        
        # initialize kmeans clustering protocol to extract centroids
        k_means = cluster.KMeans(n_clusters=4, n_init=4)
        # initialize data structures for stimulus type 
        experimental_stimuli[i_type], answer_key[i_type] = {} , {}

        for i_file in [i for i in os.listdir(os.path.join(stimulus_directory, i_folder)) if 'jpg' in i]:

            # load image
            i_image = np.array(Image.open(os.path.join(stimulus_directory, i_folder, i_file)))
            ###### kmeans segmentation protocol ######
            # binarize layer of image
            binary = i_image[:,:] != 255
            # convert binaryized image into a vector for each non-blank location
            points = [[i,j] for i in  range(binary.shape[0]) for j in range(binary.shape[1]) if binary[i,j]]
            # cluster non-blank locations to determine object center of masses
            k_means.fit(points)
            # determine mapping between cluster order and image order
            order = determine_order_of_clusters(k_means.cluster_centers_, i_image)
            ###### segmentation complete ######

            # iterate over all objects in image
            i_slide = []
            for i_segmented_object in range(len(order)):
                
                # identify centroid of each object
                x, y = k_means.cluster_centers_[order[i_segmented_object],:]
                # select an area around the center of mass defined above
                i_object =  i_image[int(x-w):int(x+w), int(y-h):int(y+h)]
                # resize image of object 
                i_object = imresize(i_object, (224, 224))
                # reshape object image 
                i_object = np.repeat(i_object[ :, : , np.newaxis], 3, axis=2)
                # append image of object to trial 
                i_slide.append(i_object)

            # save stimuli
            experimental_stimuli[i_type][i_file] = np.array( i_slide )
            # save answer
            answer_key[i_type][i_file] = int(i_file[-5])-1

    return experimental_stimuli, answer_key


def extract_model_responses(vgg, session, experimental_stimuli): 
    """return model responses to stimuli"""    

    # determine model layers to extract and their names
    layer_map = {'conv1_1': vgg.conv1_1, 'conv1_2':vgg.conv1_2, 'pool1': vgg.pool1, 
                 'conv2_1': vgg.conv2_1, 'conv2_2':vgg.conv2_2, 'pool2': vgg.pool2, 
                 'conv3_1': vgg.conv3_1, 'conv3_2':vgg.conv3_2, 'conv3_3':vgg.conv3_3, 'pool3': vgg.pool3, 
                 'conv4_1': vgg.conv4_1, 'conv4_2':vgg.conv4_2, 'conv4_3':vgg.conv4_3, 'pool4': vgg.pool4, 
                 'conv5_1': vgg.conv5_1, 'conv5_2':vgg.conv5_2, 'conv5_3':vgg.conv5_3, 'pool5': vgg.pool5, 
                 'fc6': vgg.fc1, 'fc7':vgg.fc2, 'fc8':vgg.fc3l}
    
    # initialize data structure 
    model_responses = {e:[] for e in list(experimental_stimuli)}
    # manually determine the number of images to use in trial 
    n_images = 4 

    for i_experiment in list(experimental_stimuli):

        print(i_experiment, end=' ')
        # initialize data structures 
        model_responses[i_experiment] = {} 
        
        for i_trial in list(experimental_stimuli[i_experiment]):
            
            # initialize data structure for trial 
            model_responses[i_experiment][i_trial] = {} 
            # repeat in z and then expand the first index
            i_images = experimental_stimuli[i_experiment][i_trial]
            # extract model representations 
            i_responses = session.run([[layer_map[i] for i in layer_map]], feed_dict={vgg.imgs: i_images})[0]

            for i in range(len(list(layer_map))): 
            
                # store pixel responses 
                model_responses[i_experiment][i_trial]['pixel'] = np.reshape( i_images, (n_images, -1))
                # reshape model responses to trial 
                i_response_formatted = np.reshape( i_responses[i], (n_images, -1))
                # store and name model responses 
                model_responses[i_experiment][i_trial][list(layer_map)[i]] = i_response_formatted 
    
    return model_responses

def determine_model_performance(model_responses):
    """returns model performance on experiments"""
    
    # initialize data structures
    model_performance = {}
    
    for i_experiment in list(model_responses):
        
        # determine trials to model 
        trials = list(model_responses[i_experiment])
        # determine layers to operate over
        layers = list( model_responses[i_experiment][trials[0]] )
        # extract the number of stimuli 
        n_stimuli = len(model_responses[i_experiment][trials[0]][layers[0]])
        # convenience structure for extracting off diagonal 
        x = np.array(list(range(n_stimuli)))
        # initialize data structure 
        model_performance[i_experiment] = {}

        for i_layer in layers:
            
            # initialize data structure 
            accuracy = []

            for i_trial in trials:
                
                # determine item-by-item covariance matrix from model responses to trial 
                trial_covariance = np.corrcoef(model_responses[i_experiment][i_trial][i_layer])
                # extract off diagonal from covariance matrix 
                trial_decision_space = np.array([trial_covariance[i, x[x!=i]] for i in x])
                # sort off diagonal responses 
                trial_decision_space.sort()
                # determine model-selected oddity 
                i_choice = trial_decision_space[:,-1].argmin()
                # determine accuracy of model-selected oddity 
                i_correct = i_choice == int(answer_key[i_experiment][i_trial])
                # append accuracy 
                accuracy.append( i_correct )
            
            # store model accuracy
            model_performance[i_experiment][i_layer] = np.mean( accuracy )
    
    # save model performance
    with open('model_performance.pickle', 'wb') as handle:
        pickle.dump(model_performance, handle)

    return model_performance


if __name__ == '__main__': 
   
    # set base directory all analyses are contained within
    base_directory = os.path.abspath('..')
    # set path to experimental stimuli
    stimulus_path = os.path.join(base_directory, 'experiments/lee_2006/stimuli')
    # load stimuli 
    experimental_stimuli, answer_key = extract_stimuli( stimulus_path )
    # set path to model 
    model_path = os.path.join(base_directory, 'models') 
    # load model 
    model, session = define_model( model_path ) 
    # loading model responses to stimuli') 
    model_responses = extract_model_responses( model, session, experimental_stimuli)
    # determine model performance') 
    model_performance = determine_model_performance( model_responses )
    # results saved in "model_performance.pickle" 
