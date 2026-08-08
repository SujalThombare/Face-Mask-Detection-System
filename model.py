import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import cv2
from PIL import Image
from sklearn.model_selection import train_test_split

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0' #these statements are here because there are warnings of tensorflows new version so i wanted to hide it thats why i used this and its better for mathematical operations and accuracy of model
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


#seeing the with mask images fiels
with_mask_file=os.listdir("C:/Users/tusha/Downloads/mask_detection_application/mask_detection_application/data/with_mask")

print(with_mask_file[:5])
print(with_mask_file[-5:])
#seeing the without mask images fiels
without_mask_file=os.listdir("C:/Users/tusha/Downloads/mask_detection_application/mask_detection_application/data/without_mask")

print(without_mask_file[:5])
print(without_mask_file[-5:])

print("number of with mask images:",len(with_mask_file))
print("number of without mask images:",len(without_mask_file))

#Creating labels for the two class of images---
#person with mask--> 1
#person without mask-->0

with_mask_label=[1]*len(with_mask_file)
without_mask_label=[0]*len(without_mask_file)

#checking the labels of with mask
print(with_mask_label[:5])
print(with_mask_label[-5:])

#checking the labels of without mask
print(without_mask_label[:5])
print(without_mask_label[-5:])

#checking the length of labels
print("number of with mask labels:",len(with_mask_label))
print("number of without mask labels:",len(without_mask_label))

labels=with_mask_label+without_mask_label

#displaying images using Matplotlib
#with mask image
img=mpimg.imread("C:/Users/tusha/Downloads/mask_detection_application/mask_detection_application/data/with_mask/with_mask_1545.jpg")
imageplot=plt.imshow(img)
plt.show()

#without mask image
img1=mpimg.imread("C:/Users/tusha/Downloads/mask_detection_application/mask_detection_application/data/without_mask/without_mask_996.jpg")
imageplot1=plt.imshow(img1)
plt.show()

#image processing
#1.Resizing the images
#2.convert images to numpy Arrays


with_mask_path="C:/Users/tusha/Downloads/mask_detection_application/mask_detection_application/data/with_mask/"

data=[]
for img_file in with_mask_file:
    image=Image.open(with_mask_path + img_file)#reading the image
    image=image.resize((128,128))#rezing the images to make all images of same size
    image=image.convert("RGB")#converting images into there RGB values
    image=np.array(image)#converting images into Array
    data.append(image)
    
without_mask_path="C:/Users/tusha/Downloads/mask_detection_application/mask_detection_application/data/without_mask/"


for img_file in without_mask_file:
    image=Image.open(without_mask_path + img_file)#reading the image
    image=image.resize((128,128))#rezing the images to make all images of same size
    image=image.convert("RGB")#converting images into there RGB values
    image=np.array(image)#converting images into Array
    data.append(image)

print(len(data))#checking that values are get perfectly appended
print(data[0].shape)#checking that images are resized or not

#converting images list and labels to numpy arrays
X=np.array(data)
y=np.array(labels)

print(X.shape)
print(y.shape)

#TRAIN TEST SPLIT
x_train,x_test,y_train,y_test=train_test_split(X,y,test_size=0.2,random_state=2)#assigned 20% data for testing and 80% for training
print(X.shape,x_train.shape,x_test.shape)#checking that everything is assigned correctly

#scalling the data
x_train_scaled=x_train/255
x_test_scaled=x_test/255

#Building a Convonutional Neural Network(CNN)
import tensorflow as tf  #developed by google
from tensorflow import keras

no_of_classes=2
model=keras.Sequential()

model.add(keras.layers.Conv2D(32,kernel_size=(3,3),activation="relu",input_shape=(128,128,3)))
model.add(keras.layers.MaxPooling2D(pool_size=(2,2)))

model.add(keras.layers.Conv2D(64,kernel_size=(3,3),activation="relu"))
model.add(keras.layers.MaxPooling2D(pool_size=(2,2)))
model.add(keras.layers.Flatten())

model.add(keras.layers.Dense(128,activation="relu"))
model.add(keras.layers.Dropout(0.5))

model.add(keras.layers.Dense(64,activation="relu"))
model.add(keras.layers.Dropout(0.5))

model.add(keras.layers.Dense(no_of_classes,activation="sigmoid"))

#Compile the Neural Network
model.compile(optimizer="adam",loss="sparse_categorical_crossentropy",metrics=["acc"])

#Training the neural network
history= model.fit(x_train_scaled,y_train,validation_split=0.1,epochs=20)



#model evalution
loss,accuracy=model.evaluate(x_test_scaled,y_test)
print("Test Accuracy",accuracy)

#saving my model
model.save('model1.keras')

h=history

#Visualizing the Loss Value
plt.plot(h.history["loss"],label="Train loss")
plt.plot(h.history["val_loss"],label="Validation Loss")
plt.legend()
plt.show()


#Visualizing the Accuracy Value
plt.plot(h.history["acc"],label="Train loss")
plt.plot(h.history["val_acc"],label="Validation Loss")
plt.legend()
plt.show()

