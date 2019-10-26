#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''
**********************************************************
* SpectraKeras_CNN Classifier and Regressor
* 20191025e
* Uses: TensorFlow
* By: Nicola Ferralis <feranick@hotmail.com>
***********************************************************
'''
print(__doc__)

import numpy as np
import sys, os.path, getopt, time, configparser, pickle, h5py, csv, glob
from libSpectraKeras import *

#***************************************************
# This is needed for installation through pip
#***************************************************
def SpectraKeras_CNN():
    main()

#************************************
# Parameters
#************************************
class Conf():
    def __init__(self):
        confFileName = "SpectraKeras_CNN.ini"
        self.configFile = os.getcwd()+"/"+confFileName
        self.conf = configparser.ConfigParser()
        self.conf.optionxform = str
        if os.path.isfile(self.configFile) is False:
            print(" Configuration file: \""+confFileName+"\" does not exist: Creating one.\n")
            self.createConfig()
        self.readConfig(self.configFile)
        self.model_directory = "./"
        if self.regressor:
            self.modelName = "model_regressor_CNN.hd5"
            self.summaryFileName = "summary_regressor_CNN.csv"
            self.model_png = self.model_directory+"/model_regressor_CNN.png"
        else:
            self.modelName = "model_classifier_CNN.hd5"
            self.summaryFileName = "summary_classifier_CNN.csv"
            self.model_png = self.model_directory+"/model_classifier_CNN.png"
    
        self.tb_directory = "model_CNN"
        self.model_name = self.model_directory+self.modelName
        self.model_le = self.model_directory+"model_le.pkl"
        self.spectral_range = "model_spectral_range.pkl"
        
        self.actPlotTrain = self.model_directory+"/model_CNN_conv1d-activations.png"
        self.actPlotPredict = self.model_directory+"/model_CNN_activations_"
        self.sizeColPlot = 1
    
        self.edgeTPUSharedLib = "libedgetpu.so.1"
            
    def SKDef(self):
        self.conf['Parameters'] = {
            'regressor' : False,
            'normalize' : False,
            'l_rate' : 0.001,
            'l_rdecay' : 1e-4,
            'CL_filter' : [1],
            'CL_size' : [10],
            'max_pooling' : [20],
            'dropCNN' : [0],
            'HL' : [40,70],
            'dropFCL' : 0,
            'l2' : 1e-4,
            'epochs' : 100,
            'cv_split' : 0.01,
            'fullSizeBatch' : False,
            'batch_size' : 64,
            'numLabels' : 1,
            'plotWeightsFlag' : False,
            'plotActivations' : False,
            'showValidPred' : False,
            }

    def sysDef(self):
        self.conf['System'] = {
            'makeQuantizedTFlite' : True,
            'useTFlitePred' : False,
            'TFliteRuntime' : False,
            'runCoralEdge' : False,
            }

    def readConfig(self,configFile):
        try:
            self.conf.read(configFile)
            self.SKDef = self.conf['Parameters']
            self.sysDef = self.conf['System']
        
            self.regressor = self.conf.getboolean('Parameters','regressor')
            self.normalize = self.conf.getboolean('Parameters','normalize')
            self.l_rate = self.conf.getfloat('Parameters','l_rate')
            self.l_rdecay = self.conf.getfloat('Parameters','l_rdecay')
            self.CL_filter = eval(self.SKDef['CL_filter'])
            self.CL_size = eval(self.SKDef['CL_size'])
            self.max_pooling = eval(self.SKDef['max_pooling'])
            self.dropCNN = eval(self.SKDef['dropCNN'])
            self.HL = eval(self.SKDef['HL'])
            self.dropFCL = self.conf.getfloat('Parameters','dropFCL')
            self.l2 = self.conf.getfloat('Parameters','l2')
            self.epochs = self.conf.getint('Parameters','epochs')
            self.cv_split = self.conf.getfloat('Parameters','cv_split')
            self.fullSizeBatch = self.conf.getboolean('Parameters','fullSizeBatch')
            self.batch_size = self.conf.getint('Parameters','batch_size')
            self.numLabels = self.conf.getint('Parameters','numLabels')
            self.plotWeightsFlag = self.conf.getboolean('Parameters','plotWeightsFlag')
            self.plotActivations = self.conf.getboolean('Parameters','plotActivations')
            self.showValidPred = self.conf.getboolean('Parameters','showValidPred')
            self.makeQuantizedTFlite = self.conf.getboolean('System','makeQuantizedTFlite')
            self.useTFlitePred = self.conf.getboolean('System','useTFlitePred')
            self.TFliteRuntime = self.conf.getboolean('System','TFliteRuntime')
            self.runCoralEdge = self.conf.getboolean('System','runCoralEdge')
        except:
            print(" Error in reading configuration file. Please check it\n")

    # Create configuration file
    def createConfig(self):
        try:
            self.SKDef()
            self.sysDef()
            with open(self.configFile, 'w') as configfile:
                self.conf.write(configfile)
        except:
            print("Error in creating configuration file")

#************************************
# Main
#************************************
def main():
    start_time = time.perf_counter()
    dP = Conf()
    
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "tnpbh:", ["train", "net", "predict", "batch", "help"])
    except:
        usage()
        sys.exit(2)

    if opts == []:
        usage()
        sys.exit(2)

    for o, a in opts:
        if o in ("-t" , "--train"):
            try:
                if len(sys.argv)<4:
                    train(sys.argv[2], None, False)
                else:
                    train(sys.argv[2], sys.argv[3], False)
            except:
                usage()
                sys.exit(2)

        if o in ("-n" , "--net"):
            try:
                if len(sys.argv)<4:
                    train(sys.argv[2], None, True)
                else:
                    train(sys.argv[2], sys.argv[3], True)
            except:
                usage()
                sys.exit(2)

        if o in ("-p" , "--predict"):
            try:
                predict(sys.argv[2])
            except:
                usage()
                sys.exit(2)
                
        if o in ("-b" , "--batch"):
            try:
                batchPredict(sys.argv[2])
            except:
                usage()
                sys.exit(2)

    total_time = time.perf_counter() - start_time
    print(" Total time: {0:.1f}s or {1:.1f}m or {2:.1f}h".format(total_time,
                            total_time/60, total_time/3600),"\n")

#************************************
# Training
#************************************
def train(learnFile, testFile, flag):
    dP = Conf()
    
    def_mae = 'mae'
    def_val_mae = 'val_mae'
    
    import tensorflow as tf
    import tensorflow.keras as keras
    from pkg_resources import parse_version

    if parse_version(tf.version.VERSION) < parse_version('2.0.0'):
        useTF2 = False
    else:
        useTF2 = True
    
    if useTF2:
        opts = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=1)     # Tensorflow 2.0
        conf = tf.compat.v1.ConfigProto(gpu_options=opts)  # Tensorflow 2.0
        
        #gpus = tf.config.experimental.list_physical_devices('GPU')
        #if gpus:
        #   for gpu in gpus:
        #       tf.config.experimental.set_memory_growth(gpu, True)
        #   if dP.setMaxMem:
        #       tf.config.experimental.set_virtual_device_configuration(
        #         gpus[0],
        #         [tf.config.experimental.VirtualDeviceConfiguration(memory_limit=dP.maxMem)])
        
        def_acc = 'accuracy'
        def_val_acc = 'val_accuracy'
    
    else:
        #conf.gpu_options.allow_growth = True
        opts = tf.compat.v1.GPUOptions(per_process_gpu_memory_fraction=1)
        conf = tf.compat.v1.ConfigProto(gpu_options=opts)
    
        tf.compat.v1.Session(config=conf)
        
        def_mae = 'mean_absolute_error'
        def_val_mae = 'val_mean_absolute_error'
        def_acc = 'acc'
        def_val_acc = 'val_acc'
        
    learnFileRoot = os.path.splitext(learnFile)[0]
    En, A, Cl = readLearnFile(learnFile, dP)
    if testFile != None:
        En_test, A_test, Cl_test = readLearnFile(testFile, dP)
        totA = np.vstack((A, A_test))
        totCl = np.append(Cl, Cl_test)
    else:
        totA = A
        totCl = Cl

    if flag == False:
        with open(dP.spectral_range, 'ab') as f:
            f.write(pickle.dumps(En))

    print("  Total number of points per data:",En.size)
    print("  Number of learning labels: {0:d}\n".format(int(dP.numLabels)))
    
    if dP.regressor:
        Cl2 = np.copy(Cl)
        if testFile != None:
            Cl2_test = np.copy(Cl_test)
    else:
    
        #************************************
        # Label Encoding
        #************************************
        '''
        # sklearn preprocessing is only for single labels
        from sklearn import preprocessing
        le = preprocessing.LabelEncoder()
        totCl2 = le.fit_transform(totCl)
        Cl2 = le.transform(Cl)
        if testFile != None:
            Cl2_test = le.transform(Cl_test)
        '''
        le = MultiClassReductor()
        le.fit(np.unique(totCl, axis=0))
        Cl2 = le.transform(Cl)
    
        print("  Number unique classes (training): ", np.unique(Cl).size)
    
        if testFile != None:
            Cl2_test = le.transform(Cl_test)
            print("  Number unique classes (validation):", np.unique(Cl_test).size)
            print("  Number unique classes (total): ", np.unique(totCl).size)
            
        if flag == False:
            print("\n  Label Encoder saved in:", dP.model_le,"\n")
            with open(dP.model_le, 'ab') as f:
                f.write(pickle.dumps(le))

        #totCl2 = keras.utils.to_categorical(totCl2, num_classes=np.unique(totCl).size)
        Cl2 = keras.utils.to_categorical(Cl2, num_classes=np.unique(totCl).size+1)
        if testFile != None:
            Cl2_test = keras.utils.to_categorical(Cl2_test, num_classes=np.unique(totCl).size+1)

    #************************************
    # Training
    #************************************

    if dP.fullSizeBatch == True:
        dP.batch_size = A.shape[0]

    #************************************
    # CNN specific
    # Format spectra as images for loading
    #************************************
    x_train = formatForCNN(A)
    if testFile != None:
        x_test = formatForCNN(A_test)

    #************************************
    ### Define optimizer
    #************************************
    #optim = opt.SGD(lr=0.0001, decay=1e-6, momentum=0.9, nesterov=True)
    optim = keras.optimizers.Adam(lr=dP.l_rate, beta_1=0.9,
                    beta_2=0.999, epsilon=1e-08,
                    decay=dP.l_rdecay,
                    amsgrad=False)
    #************************************
    ### Build model
    #************************************
    model = keras.models.Sequential()

    for i in range(len(dP.CL_filter)):
        model.add(keras.layers.Conv2D(dP.CL_filter[i], (1, dP.CL_size[i]),
            activation='relu',
            input_shape=x_train[0].shape))
        model.add(keras.layers.Dropout(dP.dropCNN[i]))
        try:
            model.add(keras.layers.MaxPooling2D(pool_size=(1, dP.max_pooling[i])))
        except:
            print("  WARNING: Pooling layer is larger than last convolution layer\n  Aborting\n")
            return
    '''
    try:
        model.add(keras.layers.MaxPooling2D(pool_size=(1, dP.max_pooling)))
    except:
        if dP.max_pooling > dP.CL_size[-1]:
            dP.max_pooling -= dP.CL_size[-1] - 1
            print(" Rescaled pool size: ", dP.max_pooling, "\n")
            model.add(keras.layers.MaxPooling2D(pool_size=(1, dP.max_pooling)))
        else:
            print(" Final conv-layer needs to be smaller than pooling layer")
            return
    '''
    model.add(keras.layers.Flatten())

    for i in range(len(dP.HL)):
        model.add(keras.layers.Dense(dP.HL[i],
            activation = 'relu',
            input_dim=A.shape[1],
            kernel_regularizer=keras.regularizers.l2(dP.l2)))
        model.add(keras.layers.Dropout(dP.dropFCL))

    if dP.regressor:
        model.add(keras.layers.Dense(1))
        model.compile(loss='mse',
        optimizer=optim,
        metrics=['mae'])
    else:
        model.add(keras.layers.Dense(np.unique(totCl).size+1, activation = 'softmax'))
        model.compile(loss='categorical_crossentropy',
            optimizer=optim,
            metrics=['accuracy'])

    tbLog = keras.callbacks.TensorBoard(log_dir=dP.tb_directory, histogram_freq=120,
            write_graph=True, write_images=True)
    tbLogs = [tbLog]
    
    model.summary()
    
    if flag:
        return
    
    if testFile != None:
        log = model.fit(x_train, Cl2,
            epochs=dP.epochs,
            batch_size=dP.batch_size,
            callbacks = tbLogs,
            verbose=2,
            validation_data=(x_test, Cl2_test))
    else:
        log = model.fit(x_train, Cl2,
            epochs=dP.epochs,
            batch_size=dP.batch_size,
            callbacks = tbLogs,
            verbose=2,
	        validation_split=dP.cv_split)

    # Plot activations
    if dP.plotActivations:
        plotActivationsTrain(model)

    if useTF2:
        model.save(dP.model_name, save_format='h5')
    else:
        model.save(dP.model_name)
    keras.utils.plot_model(model, to_file=dP.model_png, show_shapes=True)
    model.summary()
    
    if dP.makeQuantizedTFlite:
        makeQuantizedTFmodel(x_train, model, dP)

    print('\n  =============================================')
    print('  \033[1m CNN\033[0m - Model Configuration')
    print('  =============================================')

    print("  Training set file:",learnFile)
    print("  Data size:", A.shape,"\n")
    print("  Number of learning labels:",dP.numLabels)
    print("  Total number of points per data:",En.size)

    loss = np.asarray(log.history['loss'])
    val_loss = np.asarray(log.history['val_loss'])

    if dP.regressor:
        val_mae = np.asarray(log.history[def_val_mae])
        printParam()
        print('\n  ==========================================================')
        print('  \033[1m CNN - Regressor\033[0m - Training Summary')
        print('  ==========================================================')
        print("  \033[1mLoss\033[0m - Average: {0:.4f}; Min: {1:.4f}; Last: {2:.4f}".format(np.average(loss), np.amin(loss), loss[-1]))
        print('\n\n  ==========================================================')
        print('  \033[1m CNN - Regressor \033[0m - Validation Summary')
        print('  ========================================================')
        print("  \033[1mLoss\033[0m - Average: {0:.4f}; Min: {1:.4f}; Last: {2:.4f}".format(np.average(val_loss), np.amin(val_loss), val_loss[-1]))
        print("  \033[1mMean Abs Err\033[0m - Average: {0:.4f}; Min: {1:.4f}; Last: {2:.4f}\n".format(np.average(val_mae), np.amin(val_mae), val_mae[-1]))
        print('  ========================================================\n')
        if testFile != None and dP.showValidPred:
            predictions = model.predict(A_test)
            print('  ========================================================')
            print("  Real value | Predicted value | val_loss | val_mean_abs_err")
            print("  -----------------------------------------------------------")
            for i in range(0,len(predictions)):
                score = model.evaluate(np.array([x_test[i]]), np.array([Cl_test[i]]), batch_size=dP.batch_size, verbose = 0)
                print("  {0:.2f}\t\t| {1:.2f}\t\t| {2:.4f}\t| {3:.4f} ".format(Cl2_test[i],
                    predictions[i][0], score[0], score[1]))
            print('\n  ==========================================================\n')
    else:
        accuracy = np.asarray(log.history[def_acc])
        val_acc = np.asarray(log.history[def_val_acc])
        print("  Number unique classes (training): ", np.unique(Cl).size)
        if testFile != None:
            Cl2_test = le.transform(Cl_test)
            print("  Number unique classes (validation):", np.unique(Cl_test).size)
            print("  Number unique classes (total): ", np.unique(totCl).size)
        printParam()
        print('\n  ========================================================')
        print('  \033[1m CNN - Classifier \033[0m - Training Summary')
        print('  ========================================================')
        print("\n  \033[1mAccuracy\033[0m - Average: {0:.2f}%; Max: {1:.2f}%; Last: {2:.2f}%".format(100*np.average(accuracy),
            100*np.amax(accuracy), 100*accuracy[-1]))
        print("  \033[1mLoss\033[0m - Average: {0:.4f}; Min: {1:.4f}; Last: {2:.4f}".format(np.average(loss), np.amin(loss), loss[-1]))
        print('\n\n  ========================================================')
        print('  \033[1m CNN - Classifier \033[0m - Validation Summary')
        print('  ========================================================')
        print("\n  \033[1mAccuracy\033[0m - Average: {0:.2f}%; Max: {1:.2f}%; Last: {2:.2f}%".format(100*np.average(val_acc),
        100*np.amax(val_acc), 100*val_acc[-1]))
        print("  \033[1mLoss\033[0m - Average: {0:.4f}; Min: {1:.4f}; Last: {2:.4f}\n".format(np.average(val_loss), np.amin(val_loss), val_loss[-1]))
        print('  ========================================================\n')
        if testFile != None and dP.showValidPred:
            print("  Real class\t| Predicted class\t| Probability")
            print("  ---------------------------------------------------")
            predictions = model.predict(x_test)
            for i in range(predictions.shape[0]):
                predClass = np.argmax(predictions[i])
                predProb = round(100*predictions[i][predClass],2)
                predValue = le.inverse_transform(predClass)[0]
                realValue = Cl_test[i]
                print("  {0:.2f}\t\t| {1:.2f}\t\t\t| {2:.2f}".format(realValue, predValue, predProb))
            #print("\n  Validation - Loss: {0:.2f}; accuracy: {1:.2f}%".format(score[0], 100*score[1]))
            print('\n  ========================================================\n')

    if dP.plotWeightsFlag == True:
        plotWeights(En, A, model, "CNN")

    getTFVersion(dP)

#************************************
# Prediction
#************************************
def predict(testFile):
    dP = Conf()
    model = loadModel(dP)

    R, good = readTestFile(testFile, dP)
    if not good:
        return
    R = formatForCNN(R)

    if dP.regressor:
        #predictions = model.predict(R).flatten()[0]
        predictions = getPredictions(R, model, dP).flatten()[0]
        print('\n  ========================================================')
        print('  \033[1m CNN - Regressor\033[0m - Prediction')
        print('  ========================================================')
        predValue = predictions
        print('\033[1m\n  Predicted value (normalized) = {0:.2f}\033[0m\n'.format(predValue))
        print('  ========================================================\n')
        
    else:
        le = pickle.loads(open(dP.model_le, "rb").read())
        #predictions = model.predict(R, verbose=0)
        predictions = getPredictions(R, model,dP)
        pred_class = np.argmax(predictions)
        if dP.useTFlitePred:
            predProb = round(100*predictions[0][pred_class]/255,2)
        else:
            predProb = round(100*predictions[0][pred_class],2)
        rosterPred = np.where(predictions[0]>0.1)[0]
        print('\n  ========================================================')
        print('  \033[1m CNN - Classifier\033[0m - Prediction')
        print('  ========================================================')

        if dP.numLabels == 1:
            if pred_class.size >0:
                predValue = le.inverse_transform(pred_class)[0]
            else:
                predValue = 0
            print('  Prediction\t| Probability [%]')
            print('  ----------------------------- ')
            for i in range(len(predictions[0])-1):
                if predictions[0][i]>0.01:
                    if dP.useTFlitePred:
                        print("  {0:.2f}\t\t| {1:.2f}".format(le.inverse_transform(i)[0],100*predictions[0][i]/255))
                    else:
                        print("  {0:.2f}\t\t| {1:.2f}".format(le.inverse_transform(i)[0],100*predictions[0][i]))
            print('\033[1m\n  Predicted value = {0:.2f} (probability = {1:.2f}%)\033[0m\n'.format(predValue, predProb))
            print('  ========================================================\n')

        else:
            print('\n ==========================================')
            print('\033[1m' + ' Predicted value \033[0m(probability = ' + str(predProb) + '%)')
            print(' ==========================================\n')
            print("  1:", str(predValue[0]),"%")
            print("  2:",str(predValue[1]),"%")
            print("  3:",str((predValue[1]/0.5)*(100-99.2-.3)),"%\n")
            print(' ==========================================\n')

    if dP.plotActivations and not dP.useTFlitePred:
        plotActivationsPredictions(R,model)

#************************************
# Batch Prediction
#************************************
def batchPredict(folder):
    dP = Conf()
    model = loadModel(dP)

    predictions = np.zeros((0,0))
    fileName = []
    for file in glob.glob(folder+'/*.txt'):
        R, good = readTestFile(file, dP)
        if good:
            R = formatForCNN(R)
            try:
                predictions = np.vstack((predictions,getPredictions(R, model, dP).flatten()))
            except:
                predictions = np.array([getPredictions(R, model,dP).flatten()])
            fileName.append(file)

    if dP.regressor:
        summaryFile = np.array([['SpectraKeras_CNN','Regressor','',],['File name','Prediction','']])
        print('\n  ========================================================')
        print('  \033[1m CNN - Regressor\033[0m - Prediction')
        print('  ========================================================')
        for i in range(predictions.shape[0]):
            predValue = predictions[i][0]
            print('  {0:s}:\033[1m\n   Predicted value = {1:.2f}\033[0m\n'.format(fileName[i],predValue))
            summaryFile = np.vstack((summaryFile,[fileName[i],predValue,'']))
        print('  ========================================================\n')

    else:
        le = pickle.loads(open(dP.model_le, "rb").read())
        summaryFile = np.array([['SpectraKeras_CNN','Classifier',''],['File name','Predicted Class', 'Probability']])
        print('\n  ========================================================')
        print('  \033[1m CNN - Classifier\033[0m - Prediction')
        print('  ========================================================')
        for i in range(predictions.shape[0]):
            pred_class = np.argmax(predictions[i])
            if dP.useTFlitePred:
                predProb = round(100*predictions[i][pred_class]/255,2)
            else:
                predProb = round(100*predictions[i][pred_class],2)
            rosterPred = np.where(predictions[i][0]>0.1)[0]
        
            if pred_class.size >0:
                predValue = le.inverse_transform(pred_class)[0]
                print('  {0:s}:\033[1m\n   Predicted value = {1:.2f} (probability = {2:.2f}%)\033[0m\n'.format(fileName[i],predValue, predProb))
            else:
                predValue = 0
                print('  {0:s}:\033[1m\n   No predicted value (probability = {1:.2f}%)\033[0m\n'.format(fileName[i],predProb))
            summaryFile = np.vstack((summaryFile,[fileName[i], predValue,predProb]))
        print('  ========================================================\n')
        
    import pandas as pd
    df = pd.DataFrame(summaryFile)
    df.to_csv(dP.summaryFileName, index=False, header=False)
    print(" Prediction summary saved in:",dP.summaryFileName,"\n")

#****************************************************
# Format data for CNN
#****************************************************
def formatForCNN(A):
    listmatrix = []
    for i in range(A.shape[0]):
        spectra = np.dstack([A[i]])
        listmatrix.append(spectra)
    x = np.stack(listmatrix, axis=0)
    return x

#************************************
# Print NN Info
#************************************
def printParam():
    dP = Conf()
    print('\n  ================================================')
    print('  \033[1m CNN\033[0m - Parameters')
    print('  ================================================')
    print('  Optimizer:','Adam',
                '\n  Convolutional layers:', dP.CL_filter,
                '\n  Convolutional layers size:', dP.CL_size,
                '\n  Max Pooling:', dP.max_pooling,
                '\n  Dropout CNN:', dP.dropCNN,
                '\n  Hidden layers:', dP.HL,
                '\n  Activation function:','relu',
                '\n  L2:',dP.l2,
                '\n  Dropout HL:', dP.dropFCL,
                '\n  Learning rate:', dP.l_rate,
                '\n  Learning decay rate:', dP.l_rdecay)
    if dP.fullSizeBatch == True:
        print('  Batch size: full')
    else:
        print('  Batch size:', dP.batch_size)
    print('  Number of labels:', dP.numLabels)
    #print('  ================================================\n')


#************************************
# Plot Activations in Predictions
#************************************
def plotActivationsTrain(model):
    dP = Conf()
    col_size = dP.sizeColPlot
    row_size = int(dP.CL_filter[0])
    if row_size > 1:
        import matplotlib.pyplot as plt
        weight_conv2d_1 = model.layers[0].get_weights()[0][:,:,0,:]
        filter_index = 0
        fig, ax = plt.subplots(row_size, col_size, figsize=(row_size*3,col_size*3))
    
        for row in range(0,row_size):
            ax[row].plot(weight_conv2d_1[:,:,filter_index][0])
            filter_index += 1
            plt.savefig(dP.actPlotTrain, dpi = 160, format = 'png')  # Save plot
        '''
        for row in range(0,row_size):
            for col in range(0,col_size):
                #ax[row][col].imshow(weight_conv2d_1[:,:,filter_index],cmap="gray")
                ax[row][col].plot(weight_conv2d_1[:,:,filter_index][0])
                filter_index += 1
        '''
        #plt.show()
        plt.savefig(dP.actPlotTrain, dpi = 160, format = 'png')  # Save plot
    
#************************************
# Plot Activations in Predictions
#************************************
def plotActivationsPredictions(R, model):
    print(" Saving activation plots...\n")
    import matplotlib.pyplot as plt
    from tensorflow.keras.models import Model
    dP = Conf()
    layer_outputs = [layer.output for layer in model.layers]
    activation_model = Model(inputs=model.input, outputs=layer_outputs)
    activations = activation_model.predict(R)
    
    def display_activation(activations, layerName, col_size, layerShape, act_index):
        activation = activations[act_index]
        if len(activation_model.layers[i+1].output_shape) == 4:
            activation_index=0
            row_size = int(layerShape[3]/col_size)
            fig, ax = plt.subplots(row_size+1, col_size, figsize=(row_size*3,col_size*3))
            plt.suptitle("Prediction spectra in red, activations in blue\n Layer: "+layerName, fontsize=16)
            for col in range(0,col_size):
                ax[0][col].plot(R[0,0,:,0],'r')
            for row in range(1,row_size+1):
                for col in range(0,col_size):
                    #ax[row][col].plot(R[0,0,:,0],'r')
                    #ax[row][col].imshow(activation[0, :, :, activation_index], cmap='gray')
                    ax[row][col].plot(activation[0, :, :, activation_index][0])
                    activation_index += 1
        else:
            row_size = 2
            col_size = 1
            fig, ax = plt.subplots(row_size, col_size, figsize=(row_size*6,col_size*6))
            plt.suptitle("Prediction spectra in red, dense layers in blue\n Layer: "+layerName, fontsize=16)
            ax[0].plot(R[0,0,:,0],'r')
            ax[1].plot(activation[0])

        plt.savefig(dP.actPlotPredict+layerName+'.png', dpi = 160, format = 'png')  # Save plot

    try:
        for i in range(len(activations)):
            display_activation(activations, activation_model.layers[i+1].name, dP.sizeColPlot, activation_model.layers[i+1].output_shape, i)
    except:
        pass

#************************************
# Lists the program usage
#************************************
def usage():
    print('\n Usage:\n')
    print(' Train (Random cross validation):')
    print('  python3 SpectraKeras_CNN.py -t <learningFile>\n')
    print(' Train (with external validation):')
    print('  python3 SpectraKeras_CNN.py -t <learningFile> <validationFile>\n')
    print(' Predict:')
    print('  python3 SpectraKeras_CNN.py -p <testFile>\n')
    print(' Batch predict:')
    print('  python3 SpectraKeras_CNN.py -b <folder>\n')
    print(' Display Neural Network Configuration:')
    print('  python3 SpectraKeras_CNN.py -n <learningFile>\n')
    print(' Requires python 3.x. Not compatible with python 2.x\n')

#************************************
# Main initialization routine
#************************************
if __name__ == "__main__":
    sys.exit(main())
