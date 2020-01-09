# BgoScript

废狗半放置式挂机脚本，纯图片识别+WINAPI模拟点击， ~~写了几天挂闪闪祭用的，~~ 从闪闪祭开始挂无限池用的，纯属娱乐产物

本脚本用到的环境是一般科研狗需要的比较复杂的环境，适合有一定编程经验的人使用。

# 使用说明

1. 需要从[此处](https://zhouxuebin.club:4433/data/2020/01/fgo_new.db.zip)下载并解压数据库文件，放到`cv_data/fgo_new.db`中。 
2. 在执行脚本前需要选好队伍、助战的职介，然后进一次需要挂机的本，在选助战界面再退出来，确保界面右边任务列表中第一个为要刷的本。
3. 然后在`config.py`里面改自己的配队和过图的逻辑代码。
4. 运行脚本过程中，不要最小化模拟器，确保模拟器整个窗体在屏幕范围内，个人建议：用`Ctrl`+`Win`+`D`新建一个桌面，把脚本和模拟器都放在该桌面运行，使用`Ctrl`+`Win`+`←`或`→`切换桌面。
5. 确保你当前的编队是即将进本的编队，选择助战后会直接跳过编队选择进本。
6. 不要把模拟器窗口调得太小，自己看着都难受，图片识别效果肯定也部邢。

本脚本自动执行的操作为：
- 自动啃苹果（金苹果）
- 点击第一个本
- 根据队伍配置自动选择符合从者和礼装的助战（目前暂时未实现仅限好友/技能等级的识别）
- 自动进本
- 每T都会调用函数确定本T需要进行哪些操作（该部分由用户自己实现，在`config.py`里面修改）
- 自动出本
- 返回第一步操作，循环

# 环境需求

## Python

Python 3.6 / 3.7

其他依赖包：
- `numpy`
- `pillow`
- `scipy`
- `scikit-image` （可选）

## OpenCV 3.4.x

### 方法1

python 3.7的预编译opencv模块可以直接从[此处](https://zhouxuebin.club:4433/data/2020/01/opencv_3.4.8_msvc15_x64_py37_redist.zip)直接下载，解压到该目录即可使用。

### 方法2

简单来说就是下载OpenCV 3.4.x的源代码和contrib的代码，用cmake和(VS或GCC)编译，百度教程一大堆就不再重复叙述了。

配置cmake时需要勾上`BUILD_opencv_python3`和`OPENCV_ENABLE_NONFREE`，`OPENCV_EXTRA_MODULES_PATH`选择解压的contrib源代码下的`modules`文件夹路径，确保SIFT算法可用（识别礼装要用）。

生成的DLL需要添加到`PATH`环境变量中，确保运行如下的代码没有报错后即说明成功安装包含SIFT模块的OpenCV：
```python
import cv2
cv2.xfeatures2d_SIFT.create()
```

## Mumu模拟器

其实用其他的也行，自己继承`AbstractAttacher`实现一下查找窗体句柄（`locate_handle`）那部分代码就行。找窗体句柄可以用VS自带的`spy++`，找的时候注意这个窗体是能响应鼠标事件并且能获得屏幕截图的就行了。

注意这里要求屏幕尺寸是16:9的，否则图片识别会失效，推荐常用的分辨率是`1280x720`和`1920x1080`。

# ROADMAP

- 代码重构（咕咕咕）
- 识别助战各技能等级
- 识别助战为好友/非好友
- 自动配队

# 免责声明

本项目与本人所属的实验室团队及科研项目无关，并且仅在摸鱼时候完成。

任何使用该脚本导致账号封禁的，开发者不承担任何责任。

# 其他说明

需要更新从者/礼装数据库时，运行：
```bash
python database/crawler_main.py -o cv_data/fgo_new.db
```
需要安装的额外模块有：`requests`，`beautifulsoup4`，`pandas`


<!--
# ~~Special Thanks~~

~~某热心催促完成脚本大业的沙雕室友~~
-->

![黑贞天下第一](asset/jeannedarcalter.gif)
