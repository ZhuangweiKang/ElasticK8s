import os

images = ['docgroupvandy/xceptionkeras', 'docgroupvandy/k8s-demo', 'docgroupvandy/vgg16keras', 'docgroupvandy/vgg19keras', 'docgroupvandy/resnet50keras', 'docgroupvandy/inceptionv3keras', 'docgroupvandy/inceptionresnetv2keras', 'docgroupvandy/mobilenetkeras', 'docgroupvandy/densenet121keras', 'docgroupvandy/densenet169keras', 'docgroupvandy/densenet201keras', 'docgroupvandy/word2vec_google', 'docgroupvandy/speech-to-text-wavenet', 'docgroupvandy/word2vec_glove']

for image in images:
  command = 'docker pull ' + image
  _exec = os.popen(command)
  print(_exec.read())
