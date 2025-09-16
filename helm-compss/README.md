# Instructions for EUCNC

## B2DROP
Make sure the b2drop is mounted in agx12, agx13:

```sudo mount -a```

## Jetson Inference
Everything should be prepared under /home/vmasip/jetson-inference directory in agx13, otherwise:

```git clone gitlab  https://gitlab.bsc.es/ppc/benchmarks/ai/jetson-inference.git```

```cd jetson-inference```

```git submodule update --init```

Launch the application (camera image, jetson inference) in the agx13:

The IP in the following command should be 40 (I remember, if not search for the command).

```bash docker/run.sh --run "video-viewer data/b2drop/smartCity/barcelona/encants/videos/IMG_1834_clip.MOV rtp://239.255.12.43:5000 --input-loop=1000"```

## Camera Edge
Everything should be prepared under /home/vmasip/camera-edge directory in agx13.

By default `all_cameras_en.yaml` it is configured to run properly (you can change the number of frame images), otherwise change the values, the path it should be something /home/vmasip/camera-edge/data/all_cameras_en.yaml  

```
cd /home/vmasip/camera-edge/docker
bash rundocker.sh (something similar to this, don't remember)
```

Build inside:
```make```
Launch the app, by default :
```./edge -i ../data/all_cameras_en.yaml -s0 -v 1 -u 1 0002```


## Launch compss application
Everything should be prepared under /home/vmasip/helm-smartcity-delay-order directory on agx12.

```cd /home/vmasip/helm-smartcity-delay-order```

```helm install <compss_app> . ```

## Visualize through laptop
As I remember something similar to this:
```
gst-launch-1.0 -v  udpsrc multicast-group=239.255.12.42 port=5002 caps="application/x-rtp, media=video, encoding-name=H264, clock-rate=90000, payload=96"  ! identity name=identity_in silent=false  ! rtpjitterbuffer  ! rtph264depay  ! avdec_h264  ! videoconvert  ! autovideosink sync=false
```

### Values.yaml configuration settings to comment:
MQTT broker it is by default as true and will run on agx12 (192.168.89.254).
In order to suscribe and see the alerts on another machine in same network, make sure to have installed mosquitto_client
```
sudo apt update

sudo apt install mosquitto-clients
```

In order to see the alerts from MQTT suscribe to the MQTT broker, after helm install have been done (launched compss application).

```mosquitto_sub -h 192.168.89.254 -p 31883 -t "alerts"```

Where:
- IP (agx12): 192.168.89.254
- Port (agx12): 31883
- Topic: alerts

