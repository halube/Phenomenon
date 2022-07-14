FROM danforthcenter/plantcv

USER root

RUN conda remove -y opencv
RUN pip install 'opencv-contrib-python<4'
RUN pip install imutils
USER $NB_UID