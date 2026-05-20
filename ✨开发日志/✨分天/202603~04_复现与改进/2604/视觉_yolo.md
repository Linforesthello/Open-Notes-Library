
## windows_yolo_pytorch_gpu
### miniconda
1. ![[Pasted image 20260506155940.png]]
2. conda activate yolo![[Pasted image 20260506155913.png]]


## 第一次训练模型，成功
看到epoch

> [!NOTE]
> (yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>yolo detect train model=yolov8n.pt data=dataset.yaml epochs=50 imgsz=640
> New https://pypi.org/project/ultralytics/8.4.47 available  Update with 'pip install -U ultralytics'
> Ultralytics 8.4.46  Python-3.10.20 torch-2.5.1+cu121 CUDA:0 (NVIDIA GeForce RTX 3050 Ti Laptop GPU, 4096MiB)
> engine\trainer: agnostic_nms=False, amp=True, angle=1.0, augment=False, auto_augment=randaugment, batch=16, bgr=0.0, box=7.5, cache=False, cfg=None, classes=None, close_mosaic=10, cls=0.5, cls_pw=0.0, compile=False, conf=None, copy_paste=0.0, copy_paste_mode=flip, cos_lr=False, cutmix=0.0, data=dataset.yaml, degrees=0.0, deterministic=True, device=None, dfl=1.5, dnn=False, dropout=0.0, dynamic=False, embed=None, end2end=None, epochs=50, erasing=0.4, exist_ok=False, fliplr=0.5, flipud=0.0, format=torchscript, fraction=1.0, freeze=None, half=False, hsv_h=0.015, hsv_s=0.7, hsv_v=0.4, imgsz=640, int8=False, iou=0.7, keras=False, kobj=1.0, line_width=None, lr0=0.01, lrf=0.01, mask_ratio=4, max_det=300, mixup=0.0, mode=train, model=yolov8n.pt, momentum=0.937, mosaic=1.0, multi_scale=0.0, name=train-6, nbs=64, nms=False, opset=None, optimize=False, optimizer=auto, overlap_mask=True, patience=100, perspective=0.0, plots=True, pose=12.0, pretrained=True, profile=False, project=None, rect=False, resume=False, retina_masks=False, rle=1.0, save=True, save_conf=False, save_crop=False, save_dir=C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\runs\detect\train-6, save_frames=False, save_json=False, save_period=-1, save_txt=False, scale=0.5, seed=0, shear=0.0, show=False, show_boxes=True, show_conf=True, show_labels=True, simplify=True, single_cls=False, source=None, split=val, stream_buffer=False, task=detect, time=None, tracker=botsort.yaml, translate=0.1, val=True, verbose=True, vid_stride=1, visualize=False, warmup_bias_lr=0.1, warmup_epochs=3.0, warmup_momentum=0.8, weight_decay=0.0005, workers=8, workspace=None
> Downloading https://ultralytics.com/assets/Arial.ttf to 'C:\Users\86173\AppData\Roaming\Ultralytics\Arial.ttf': 2% ─────Downloading https://ultralytics.com/assets/Arial.ttf to 'C:\Users\86173\AppData\Roaming\Ultralytics\Arial.ttf': 11% ━───Downloading https://ultralytics.com/assets/Arial.ttf to 'C:\Users\86173\AppData\Roaming\Ultralytics\Arial.ttf': 21% ━━╸─Downloading https://ultralytics.com/assets/Arial.ttf to 'C:\Users\86173\AppData\Roaming\Ultralytics\Arial.ttf': 30% ━━━╸Downloading https://ultralytics.com/assets/Arial.ttf to 'C:\Users\86173\AppData\Roaming\Ultralytics\Arial.ttf': 42% ━━━━Downloading https://ultralytics.com/assets/Arial.ttf to 'C:\Users\86173\AppData\Roaming\Ultralytics\Arial.ttf': 78% ━━━━Downloading https://ultralytics.com/assets/Arial.ttf to 'C:\Users\86173\AppData\Roaming\Ultralytics\Arial.ttf': 100% ━━━━━━━━━━━━ 755.1KB 653.2KB/s 1.2s
> Overriding model.yaml nc=80 with nc=3
> 
>                    from  n    params  module                                       arguments
>   0                  -1  1       464  ultralytics.nn.modules.conv.Conv             [3, 16, 3, 2]
>   1                  -1  1      4672  ultralytics.nn.modules.conv.Conv             [16, 32, 3, 2]
>   2                  -1  1      7360  ultralytics.nn.modules.block.C2f             [32, 32, 1, True]
>   3                  -1  1     18560  ultralytics.nn.modules.conv.Conv             [32, 64, 3, 2]
>   4                  -1  2     49664  ultralytics.nn.modules.block.C2f             [64, 64, 2, True]
>   5                  -1  1     73984  ultralytics.nn.modules.conv.Conv             [64, 128, 3, 2]
>   6                  -1  2    197632  ultralytics.nn.modules.block.C2f             [128, 128, 2, True]
>   7                  -1  1    295424  ultralytics.nn.modules.conv.Conv             [128, 256, 3, 2]
>   8                  -1  1    460288  ultralytics.nn.modules.block.C2f             [256, 256, 1, True]
>   9                  -1  1    164608  ultralytics.nn.modules.block.SPPF            [256, 256, 5]
>  10                  -1  1         0  torch.nn.modules.upsampling.Upsample         [None, 2, 'nearest']
>  11             [-1, 6]  1         0  ultralytics.nn.modules.conv.Concat           [1]
>  12                  -1  1    148224  ultralytics.nn.modules.block.C2f             [384, 128, 1]
>  13                  -1  1         0  torch.nn.modules.upsampling.Upsample         [None, 2, 'nearest']
>  14             [-1, 4]  1         0  ultralytics.nn.modules.conv.Concat           [1]
>  15                  -1  1     37248  ultralytics.nn.modules.block.C2f             [192, 64, 1]
>  16                  -1  1     36992  ultralytics.nn.modules.conv.Conv             [64, 64, 3, 2]
>  17            [-1, 12]  1         0  ultralytics.nn.modules.conv.Concat           [1]
>  18                  -1  1    123648  ultralytics.nn.modules.block.C2f             [192, 128, 1]
>  19                  -1  1    147712  ultralytics.nn.modules.conv.Conv             [128, 128, 3, 2]
>  20             [-1, 9]  1         0  ultralytics.nn.modules.conv.Concat           [1]
>  21                  -1  1    493056  ultralytics.nn.modules.block.C2f             [384, 256, 1]
>  22        [15, 18, 21]  1    751897  ultralytics.nn.modules.head.Detect           [3, 16, None, [64, 128, 256]]
> Model summary: 130 layers, 3,011,433 parameters, 3,011,417 gradients, 8.2 GFLOPs
> 
> Transferred 319/355 items from pretrained weights
> Freezing layer 'model.22.dfl.conv.weight'
> AMP: running Automatic Mixed Precision (AMP) checks...
> Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 1% ──────────── 4Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 2% ──────────── 9Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 3% ──────────── 1Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 5% ╸─────────── 2Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 7% ╸─────────── 4Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 12% ━─────────── Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 19% ━━────────── Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 21% ━━╸───────── 1.1/5.3MB 555.5KDownloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26Downloading https://github.com/ultralytics/assetDownloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 31% ━━━╸──────── 1.6/5.3MB 498.3KB/s 2.0s<7.5sDownloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 41% ━━━━╸─────── 2.2/5.3MB 2.0MB/s 2.2Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 45% ━━━━━─────── 2.4/5.3MB 2.0MB/s 2.3Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 48% ━━━━━╸────── 2.5/5.3MB 1.4MB/s 2.5Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 51% ━━━━━━────── 2.7/5.3MB 1.1MB/s 2.6Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 54% ━━━━━━────── 2.9/5.3MB 1.8MB/s 2.7Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 55% ━━━━━━╸───── 2.9/5.3MB 378.4KB/s 3Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 64% ━━━━━━━╸──── 3.4/5.3MB 2.0MB/s 3.3Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 69% ━━━━━━━━──── 3.6/5.3MB 2.3MB/s 3.4Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 72% ━━━━━━━━╸─── 3.8/5.3MB 1.7MB/s 3.5Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 75% ━━━━━━━━━─── 4.0/5.3MB 1.6MB/s 3.6Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 79% ━━━━━━━━━─── 4.2/5.3MB 1.7MB/s 3.7Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 82% ━━━━━━━━━╸── 4.3/5.3MB 1.8MB/s 3.8Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 85% ━━━━━━━━━━── 4.5/5.3MB 1.2MB/s 3.9Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 89% ━━━━━━━━━━╸─ 4.7/5.3MB 2.0MB/s 4.0Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 92% ━━━━━━━━━━━─ 4.9/5.3MB 1.4MB/s 4.2Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 96% ━━━━━━━━━━━╸ 5.1/5.3MB 1.9MB/s 4.3Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 98% ━━━━━━━━━━━╸ 5.2/5.3MB 411.6KB/s 4Downloading https://github.com/ultralytics/assets/releases/download/v8.4.0/yolo26n.pt to 'yolo26n.pt': 100% ━━━━━━━━━━━━ 5.3MB 1.2MB/s 4.5s
> AMP: checks passed
> train: Fast image access  (ping: 0.00.0 ms, read: 1065.0426.8 MB/s, size: 87.7 KB)
> train: Scanning C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\labels\train... 168 images, 0 backgrounds, 0 corrupt: 100% ━━━━━━━━━━━━ 168/168 2.9Kit/s 0.1s
> train: New cache created: C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\labels\train.cache
> val: Fast image access  (ping: 0.00.0 ms, read: 615.1335.5 MB/s, size: 82.3 KB)
> val: Scanning C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\labels\train.cache... 168 images, 0 backgrounds, 0 corrupt: 100% ━━━━━━━━━━━━ 168/168  0.0s
> optimizer: 'optimizer=auto' found, ignoring 'lr0=0.01' and 'momentum=0.937' and determining best 'optimizer', 'lr0' and 'momentum' automatically...
> optimizer: AdamW(lr=0.001429, momentum=0.9) with parameter groups 57 weight(decay=0.0), 64 weight(decay=0.0005), 63 bias(decay=0.0)
> Plotting labels to C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\runs\detect\train-6\labels.jpg...
> Image sizes 640 train, 640 val
> Using 8 dataloader workers
> Logging results to C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\runs\detect\train-6
> Starting training for 50 epochs...
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>        1/50      1.99G      1.094      3.217      1.258         21        640: 100% ━━━━━━━━━━━━ 11/11 2.8it/s 3.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 4.8it/s 1.2s
>                    all        168        168      0.013          1      0.987      0.806
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>        2/50      1.99G     0.8442      1.543      1.092         16        640: 100% ━━━━━━━━━━━━ 11/11 5.0it/s 2.2s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.2it/s 1.0s
>                    all        168        168          1      0.538      0.994      0.813
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>        3/50      2.01G     0.7992      1.153      1.028         19        640: 100% ━━━━━━━━━━━━ 11/11 5.4it/s 2.0s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.4it/s 0.9s
>                    all        168        168          1      0.954      0.995      0.806
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>        4/50      1.99G     0.7807      1.135      1.004         22        640: 100% ━━━━━━━━━━━━ 11/11 5.6it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 5.8it/s 1.0s
>                    all        168        168          1      0.697      0.989      0.816
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>        5/50      1.99G     0.8752      1.106      1.054         14        640: 100% ━━━━━━━━━━━━ 11/11 5.7it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 5.9it/s 1.0s
>                    all        168        168       0.97      0.774      0.952       0.75
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>        6/50         2G     0.8728      1.204      1.052          9        640: 100% ━━━━━━━━━━━━ 11/11 5.8it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.2it/s 1.0s
>                    all        168        168      0.868      0.821      0.896      0.722
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>        7/50         2G     0.7717      1.042      1.016         15        640: 100% ━━━━━━━━━━━━ 11/11 5.9it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.5it/s 0.9s
>                    all        168        168      0.897      0.984      0.974      0.763
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>        8/50         2G     0.7888     0.9794      1.021         14        640: 100% ━━━━━━━━━━━━ 11/11 5.8it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.6it/s 0.9s
>                    all        168        168      0.822      0.923      0.897       0.74
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>        9/50         2G     0.7746     0.9159      1.003         15        640: 100% ━━━━━━━━━━━━ 11/11 6.0it/s 1.8s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.3it/s 0.9s
>                    all        168        168        0.2      0.964      0.198      0.152
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       10/50         2G     0.7895      0.928      1.019         15        640: 100% ━━━━━━━━━━━━ 11/11 5.9it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.5it/s 0.9s
>                    all        168        168      0.959          1      0.991      0.729
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       11/50         2G     0.7933      0.864      1.001         20        640: 100% ━━━━━━━━━━━━ 11/11 5.9it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.6it/s 0.9s
>                    all        168        168      0.993          1      0.994      0.819
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       12/50         2G     0.7402     0.8241      1.013         16        640: 100% ━━━━━━━━━━━━ 11/11 5.9it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.5it/s 0.9s
>                    all        168        168          1      0.997      0.995      0.824
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       13/50         2G      0.816     0.8304      1.008         23        640: 100% ━━━━━━━━━━━━ 11/11 6.0it/s 1.8s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.4it/s 0.9s
>                    all        168        168      0.206      0.988      0.204      0.166
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       14/50         2G     0.7343      0.837      1.004         17        640: 100% ━━━━━━━━━━━━ 11/11 5.8it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.5it/s 0.9s
>                    all        168        168      0.992      0.982      0.995      0.838
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       15/50         2G     0.7466     0.7457     0.9845         18        640: 100% ━━━━━━━━━━━━ 11/11 5.5it/s 2.0s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 4.6it/s 1.3s
>                    all        168        168      0.998          1      0.995      0.835
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       16/50         2G     0.7381     0.7511     0.9742         17        640: 100% ━━━━━━━━━━━━ 11/11 5.7it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 5.8it/s 1.0s
>                    all        168        168      0.982      0.995      0.994      0.859
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       17/50         2G      0.751     0.7291     0.9763         14        640: 100% ━━━━━━━━━━━━ 11/11 5.7it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 5.0it/s 1.2s
>                    all        168        168      0.999          1      0.995      0.829
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       18/50         2G     0.7188     0.6776     0.9632         19        640: 100% ━━━━━━━━━━━━ 11/11 5.5it/s 2.0s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 5.4it/s 1.1s
>                    all        168        168          1          1      0.995      0.821
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       19/50         2G     0.6997     0.6691     0.9814         25        640: 100% ━━━━━━━━━━━━ 11/11 5.3it/s 2.1s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.1it/s 1.0s
>                    all        168        168          1          1      0.995      0.847
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       20/50         2G     0.7623     0.6942     0.9927         15        640: 100% ━━━━━━━━━━━━ 11/11 5.5it/s 2.0s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.3it/s 0.9s
>                    all        168        168          1          1      0.995      0.854
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       21/50         2G     0.6869     0.6577     0.9899         16        640: 100% ━━━━━━━━━━━━ 11/11 5.9it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.5it/s 0.9s
>                    all        168        168      0.997          1      0.995      0.849
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       22/50         2G     0.6844     0.6564     0.9862         10        640: 100% ━━━━━━━━━━━━ 11/11 5.8it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.0it/s 1.0s
>                    all        168        168      0.705      0.994      0.713      0.614
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       23/50         2G     0.6695     0.6351     0.9673         17        640: 100% ━━━━━━━━━━━━ 11/11 5.8it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.3it/s 1.0s
>                    all        168        168      0.999          1      0.995      0.864
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       24/50         2G     0.6635     0.6221     0.9583         21        640: 100% ━━━━━━━━━━━━ 11/11 5.7it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 7.2it/s 0.8s
>                    all        168        168      0.999          1      0.995      0.851
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       25/50         2G     0.6647     0.5774     0.9653         18        640: 100% ━━━━━━━━━━━━ 11/11 6.0it/s 1.8s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.9it/s 0.9s
>                    all        168        168          1          1      0.995       0.83
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       26/50         2G     0.6627     0.5735     0.9638         21        640: 100% ━━━━━━━━━━━━ 11/11 5.9it/s 1.8s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 7.1it/s 0.8s
>                    all        168        168          1          1      0.995      0.874
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       27/50         2G       0.64     0.5618     0.9296         20        640: 100% ━━━━━━━━━━━━ 11/11 6.0it/s 1.8s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 7.2it/s 0.8s
>                    all        168        168          1          1      0.995      0.863
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       28/50         2G     0.6507     0.5801     0.9565         27        640: 100% ━━━━━━━━━━━━ 11/11 5.9it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.9it/s 0.9s
>                    all        168        168          1          1      0.995      0.867
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       29/50         2G      0.667     0.5719     0.9585         13        640: 100% ━━━━━━━━━━━━ 11/11 6.0it/s 1.8s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 7.1it/s 0.8s
>                    all        168        168      0.577      0.988      0.582      0.508
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       30/50         2G     0.6377      0.553     0.9508         17        640: 100% ━━━━━━━━━━━━ 11/11 5.9it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 7.0it/s 0.9s
>                    all        168        168          1          1      0.995      0.854
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       31/50         2G     0.6411     0.5312     0.9568         15        640: 100% ━━━━━━━━━━━━ 11/11 5.9it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 7.0it/s 0.9s
>                    all        168        168          1          1      0.995      0.877
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       32/50         2G     0.6204     0.5217      0.952         21        640: 100% ━━━━━━━━━━━━ 11/11 5.9it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.9it/s 0.9s
>                    all        168        168          1          1      0.995      0.877
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       33/50         2G     0.6331     0.5119     0.9592         17        640: 100% ━━━━━━━━━━━━ 11/11 6.1it/s 1.8s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 7.3it/s 0.8s
>                    all        168        168          1          1      0.995      0.871
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       34/50         2G     0.5978     0.4948     0.9281         16        640: 100% ━━━━━━━━━━━━ 11/11 6.0it/s 1.8s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 7.2it/s 0.8s
>                    all        168        168          1          1      0.995      0.864
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       35/50         2G     0.5784     0.4869     0.9366         15        640: 100% ━━━━━━━━━━━━ 11/11 6.0it/s 1.8s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 7.0it/s 0.9s
>                    all        168        168          1          1      0.995      0.883
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       36/50         2G     0.6274     0.4948     0.9489         11        640: 100% ━━━━━━━━━━━━ 11/11 5.6it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.2it/s 1.0s
>                    all        168        168          1          1      0.995      0.869
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       37/50         2G     0.6116      0.485     0.9779         15        640: 100% ━━━━━━━━━━━━ 11/11 6.0it/s 1.8s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 7.1it/s 0.8s
>                    all        168        168          1          1      0.995      0.873
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       38/50         2G     0.5771     0.4517     0.9163         22        640: 100% ━━━━━━━━━━━━ 11/11 5.7it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.4it/s 0.9s
>                    all        168        168      0.999          1      0.995      0.876
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       39/50         2G     0.5647      0.448     0.9315         14        640: 100% ━━━━━━━━━━━━ 11/11 5.8it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.8it/s 0.9s
>                    all        168        168      0.884      0.994      0.887      0.791
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       40/50         2G     0.5672     0.4512     0.9349         14        640: 100% ━━━━━━━━━━━━ 11/11 5.4it/s 2.1s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 5.6it/s 1.1s
>                    all        168        168      0.588      0.988       0.59      0.531
> Closing dataloader mosaic
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       41/50         2G     0.5159     0.5477     0.8724          8        640: 100% ━━━━━━━━━━━━ 11/11 4.9it/s 2.3s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.5it/s 0.9s
>                    all        168        168          1          1      0.995      0.881
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       42/50         2G     0.5178     0.5355     0.9038          8        640: 100% ━━━━━━━━━━━━ 11/11 5.8it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 4.9it/s 1.2s
>                    all        168        168          1          1      0.995      0.902
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       43/50         2G     0.4992     0.5118     0.9067          8        640: 100% ━━━━━━━━━━━━ 11/11 5.0it/s 2.2s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 5.4it/s 1.1s
>                    all        168        168          1          1      0.995      0.897
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       44/50         2G     0.4922     0.5014     0.8969          8        640: 100% ━━━━━━━━━━━━ 11/11 5.6it/s 2.0s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.9it/s 0.9s
>                    all        168        168          1          1      0.995      0.899
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       45/50         2G     0.4652     0.4934     0.8781          8        640: 100% ━━━━━━━━━━━━ 11/11 5.8it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.2it/s 1.0s
>                    all        168        168          1          1      0.995      0.906
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       46/50         2G     0.4464     0.4666     0.8591          8        640: 100% ━━━━━━━━━━━━ 11/11 5.7it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.0it/s 1.0s
>                    all        168        168          1          1      0.995      0.909
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       47/50         2G     0.4824     0.4763      0.869          8        640: 100% ━━━━━━━━━━━━ 11/11 5.7it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.3it/s 1.0s
>                    all        168        168          1          1      0.995      0.909
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       48/50         2G     0.4601     0.4661     0.8766          8        640: 100% ━━━━━━━━━━━━ 11/11 5.6it/s 2.0s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 5.9it/s 1.0s
>                    all        168        168          1          1      0.995      0.914
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       49/50         2G     0.4397     0.4495     0.8827          8        640: 100% ━━━━━━━━━━━━ 11/11 5.9it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.6it/s 0.9s
>                    all        168        168          1          1      0.995      0.915
> 
>       Epoch    GPU_mem   box_loss   cls_loss   dfl_loss  Instances       Size
>       50/50         2G     0.4655     0.4637     0.8652          8        640: 100% ━━━━━━━━━━━━ 11/11 5.6it/s 1.9s
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 6.0it/s 1.0s
>                    all        168        168          1          1      0.995      0.917
> 
> 50 epochs completed in 0.052 hours.
> Optimizer stripped from C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\runs\detect\train-6\weights\last.pt, 6.2MB
> Optimizer stripped from C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\runs\detect\train-6\weights\best.pt, 6.2MB
> 
> Validating C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\runs\detect\train-6\weights\best.pt...
> Ultralytics 8.4.46  Python-3.10.20 torch-2.5.1+cu121 CUDA:0 (NVIDIA GeForce RTX 3050 Ti Laptop GPU, 4096MiB)
> Model summary (fused): 73 layers, 3,006,233 parameters, 0 gradients, 8.1 GFLOPs
>                  Class     Images  Instances      Box(P          R      mAP50  mAP50-95): 100% ━━━━━━━━━━━━ 6/6 4.0it/s 1.5s
>                    all        168        168          1          1      0.995      0.917
>             volleyball        168        168          1          1      0.995      0.917
> Speed: 0.4ms preprocess, 2.1ms inference, 0.0ms loss, 1.8ms postprocess per image
> Results saved to C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\runs\detect\train-6
>  Learn more at https://docs.ultralytics.com/modes/train
> 
> (yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>
> (yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>


### 因为没有窗口跳出，ai指导删除headless，出问题，现已修复
```
(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>pip list | findstr opencv
opencv-python                  4.13.0.92
opencv-python-headless         4.13.0.92

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>pip uninstall opencv-python-headless -y
Found existing installation: opencv-python-headless 4.13.0.92
Uninstalling opencv-python-headless-4.13.0.92:
  Successfully uninstalled opencv-python-headless-4.13.0.92

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>pip install opencv-python
Requirement already satisfied: opencv-python in c:\miniconda\lininstall\envs\yolo\lib\site-packages (4.13.0.92)
Requirement already satisfied: numpy>=2 in c:\miniconda\lininstall\envs\yolo\lib\site-packages (from opencv-python) (2.2.6)

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>python
Python 3.10.20 | packaged by Anaconda, Inc. | (main, Mar 11 2026, 17:42:35) [MSC v.1942 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license" for more information.
>>> import cv2
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ModuleNotFoundError: No module named 'cv2'
>>> exit()

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>where python
C:\MiniConda\lininstall\envs\yolo\python.exe
C:\Users\86173\AppData\Local\Microsoft\WindowsApps\python.exe
C:\msys64\ucrt64\bin\python.exe

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>python -c "import sys; print(sys.executable)"
C:\MiniConda\lininstall\envs\yolo\python.exe

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>python -c "import cv2; print(cv2.__file__)"
Traceback (most recent call last):
  File "<string>", line 1, in <module>
ModuleNotFoundError: No module named 'cv2'

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>where pip
C:\MiniConda\lininstall\envs\yolo\Scripts\pip.exe

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>where python
C:\MiniConda\lininstall\envs\yolo\python.exe
C:\Users\86173\AppData\Local\Microsoft\WindowsApps\python.exe
C:\msys64\ucrt64\bin\python.exe

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>pip -V
pip 26.0.1 from C:\MiniConda\lininstall\envs\yolo\lib\site-packages\pip (python 3.10)

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>dir C:\MiniConda\lininstall\envs\yolo\Lib\site-packages | findstr cv2

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>pip uninstall opencv-python opencv-python-headless -y
Found existing installation: opencv-python 4.13.0.92
Uninstalling opencv-python-4.13.0.92:
  Successfully uninstalled opencv-python-4.13.0.92
WARNING: Skipping opencv-python-headless as it is not installed.

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>pip install numpy==1.26.4
Collecting numpy==1.26.4
  Using cached numpy-1.26.4-cp310-cp310-win_amd64.whl.metadata (61 kB)
Using cached numpy-1.26.4-cp310-cp310-win_amd64.whl (15.8 MB)
Installing collected packages: numpy
  Attempting uninstall: numpy
    Found existing installation: numpy 2.2.6
    Uninstalling numpy-2.2.6:
      Successfully uninstalled numpy-2.2.6
  WARNING: Failed to remove contents in a temporary directory 'C:\MiniConda\lininstall\envs\yolo\Lib\site-packages\~umpy.libs'.
  You can safely remove it manually.
  WARNING: Failed to remove contents in a temporary directory 'C:\MiniConda\lininstall\envs\yolo\Lib\site-packages\~umpy'.
  You can safely remove it manually.
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed. This behaviour is the source of the following dependency conflicts.
label-studio-sdk 2.0.18 requires opencv-python-headless<5.0.0,>=4.12.0, which is not installed.
ultralytics 8.4.46 requires opencv-python>=4.6.0, which is not installed.
label-studio 1.23.0 requires numpy<3.0.0,>=2.2.6, but you have numpy 1.26.4 which is incompatible.
label-studio-sdk 2.0.18 requires numpy<3.0.0,>=2.2, but you have numpy 1.26.4 which is incompatible.
Successfully installed numpy-1.26.4

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>pip install opencv-python==4.8.1.78
Collecting opencv-python==4.8.1.78
  Downloading opencv_python-4.8.1.78-cp37-abi3-win_amd64.whl.metadata (20 kB)
Requirement already satisfied: numpy>=1.21.2 in c:\miniconda\lininstall\envs\yolo\lib\site-packages (from opencv-python==4.8.1.78) (1.26.4)
Downloading opencv_python-4.8.1.78-cp37-abi3-win_amd64.whl (38.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 38.1/38.1 MB 1.3 MB/s  0:00:31
Installing collected packages: opencv-python
Successfully installed opencv-python-4.8.1.78

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>python -c "import cv2; print(cv2.__version__)"
4.8.1

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>
```
#### 修复
[ROS2 深度相机 PCL](https://chatgpt.com/c/69faccbf-c40c-8323-94eb-3717a3f56486)

> [!NOTE]
> # 🛠️ 现在最简单修复（不用重装环境）
> 
> 直接执行：
> 
> ```
> pip install opencv-python==4.8.1.78
> ```
> 
> 然后验证：
> 
> ```
> python -c "import cv2; print(cv2.__version__)"
> ```
> 
> 


```
(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>pip install opencv-python==4.8.1.78
Collecting opencv-python==4.8.1.78
  Downloading opencv_python-4.8.1.78-cp37-abi3-win_amd64.whl.metadata (20 kB)
Requirement already satisfied: numpy>=1.21.2 in c:\miniconda\lininstall\envs\yolo\lib\site-packages (from opencv-python==4.8.1.78) (1.26.4)
Downloading opencv_python-4.8.1.78-cp37-abi3-win_amd64.whl (38.1 MB)
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 38.1/38.1 MB 1.3 MB/s  0:00:31
Installing collected packages: opencv-python
Successfully installed opencv-python-4.8.1.78

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>python -c "import cv2; print(cv2.__version__)"
4.8.1

(yolo) C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset>
```

## 成功！yolo看到球体并跟踪，距离达到2m左右，非常好的
1. 170张左右的占1/4左右像素尺寸的图片，
2. label studio
	1. projects
		1. volleyball_1

[Miniconda空间查看与清理](https://chatgpt.com/c/6a0db73f-7bec-83a2-a63e-e5b15202be17)

cd C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset

yolo predict model=runs/detect/train-6/weights/best.pt source=0 show=True


### windows powershell
输入以下指令，去记事本查看历史输入指令
PS C:\Users\86173> Get-History
PS C:\Users\86173> notepad (Get-PSReadlineOption).HistorySavePath
PS C:\Users\86173>
```
& c:/MiniConda/lininstall/envs/yolo/python.exe c:/Users/86173/Desktop/ProjectRequirement/Vision/yolo/test_yolo.py
dir C:\MiniConda\lininstall\envs\yolo\Lib\site-packages | findstr cv2
dir C:\MiniConda\lininstall\envs\yolo\Lib\site-packages | findstr cv2
& c:/MiniConda/lininstall/envs/yolo/python.exe c:/Users/86173/Desktop/ProjectRequirement/Vision/yolo/test_yolo.py
git add .
git commit -m "Windows|merge commit"
git pull
& c:/MiniConda/lininstall/envs/yolo/python.exe c:/Users/86173/Desktop/ProjectRequirement/Vision/yolo/test_yolo.py
& c:/MiniConda/lininstall/envs/yolo/python.exe c:/Users/86173/Desktop/ProjectRequirement/Vision/yolo/test_yolo.py
git add .
git commit -m "Windows|提交"
git push
& C:/MiniConda/lininstall/envs/yolo/python.exe c:/Users/86173/Desktop/ProjectRequirement/Vision/yolo/other/test_yolo.py
cd runs\detect\train-6\weights
cd C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset
cd runs\detect\train-6\weights
yolo predict model=best.pt source=0 show=True
conda activate yolo
cd ..
conda activate yolo
cd C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\runs\detect\train-6\weights> 
ls
cd .\runs\
ls
cd .\detect\
cd ..
```

yolo predict model="C:\Users\86173\Desktop\ProjectRequirement\Vision\yolo\dataset\runs\detect\train-6\weights\best.pt" source=0 show=True

