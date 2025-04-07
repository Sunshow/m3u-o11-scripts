# m3u-o11-scripts

## 生成 provder.cfg

```shell
python m3u_to_provider_channels.py http://xxx/hami.m3u hami output/hami.cfg
```

## 生成 mytvsupser.cfg

```shell
python m3u_to_provider_channels_mytvsuper.py http://xxx/mytvsuper.m3u mytvsuper output/mytvsuper.cfg
```

## 切分 o11 导出的 m3u 并添加 EPG

```shell
python python o11_m3u_split_by_group.py full.m3u
```