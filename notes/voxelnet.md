

# Voxelnet

确定每个voxel的边界，从而将整体仿真空间划分为三维网体空间。

看看今天一天能完成些什么。

**洞见**：

- [ ] Quick Record——questions

      - [ ] 两件事，一是针对每个粒子生成体素需要分batch尽快解决，voxelnet中的rpn

           - [x] 首先不同场景的文件夹统一读取，最终得到所有帧的文件，每一帧加载数据时得到流体数目，针对该帧的所有流体粒子再切分batch，在针对但文件切分batch，yield返回每个batch处理的粒子数
           - [ ] voxelnet rpn

      - [x] rpn是可以为我所用的，不同尺度的region是不是可以构建不同尺度的空间采样，以建模粒子不同尺度的特征

           目前看来只能采用rpn的全卷积结构

      - [x] 不要混淆张量的维度与张量的某一维向量的长度的关系

           例如BxNx3（第三维度代表x,y,z）其实3变成8的话记录的特征多了，但是整个训练集的输入仍然还是一个三维的张量

      - [x] 提取完特征我最终得到的又是谁的加速度，如果是每一个加速度，这样现实吗？局部特征，加上全局的特征，NxM的维度得到Nx3的输出，针对Nx3的label进行损失函数的计算

           现在使用的voxel group方式提取的将会是同样的模长为8+长度为3的位置矢量（以建模粒子为中心）特征。局部和全局特征将会在voxel feature layer就进行编码

      - [x] 明确哪些是因为训练额外增加的时间，这部分时间在仿真过程中是可以避免的，其次，哪些时间是预处理需要的时间，这部分时间是不可以忽略的


          仅能减少流体粒子邻居查找的时间，但是好在是不影响固体粒子的受力。

      - [ ] 有时用的是conv2d形式的共享参数MLP，而有时又是简单的全连接层，那么什么时候用什么合适？

      - [ ] 在目标检测任务中，特征图上的坐标是如何与原图片给出的label计算偏差的

      - [ ] 关于RCNN及其中RPN的疑问

           - [ ] 2K和4Kchannels是什么意思，全连接卷积层实现RPN？

           - [ ] ROI pooling？

               RCNN如何结合不同的proposals，RoI工作原理

            - [ ] RPM的anchors和卷积层什么关系

            - [ ] 特征图+anchors= proposals 

                  仍然没有找到anchor和特征图之间的关系，而且第一部分选择完proposals之后，后面target完全没有利用，target是在做什么？

            - [ ] 不知道大家有没有想过一个问题，为什么某些情况下，网络的深度增加，但是效果却更差了，我们可以假设固定前N层，在N+1层增加一个恒等映射，这样，至少还可以取得一样的效果，但是为什么会更差呢？

                  ResNet shortcut connettion 捷径连接

            - [ ] 全卷积网络，去除所有的全连接层，全部由卷积层替代

- [ ] 数据读取

      - [x] voxel大小及仿真空间确定
      - [x] 固体粒子的坐标初始化
      - [ ] 固体采样是空心还是实心
      - [ ] 提取出的特征如何与每一个流体粒子相对应（T-net的旋转处理）
      - [ ] 准备底层数据输入与预处理方法，整理完思路之后将底层数据处理的方式提取出来

- [ ] voxel划分

      - [ ] 固体粒子添加一个属性，标注是静态还是动态，在物理仿真中其实也就不超过20个邻居粒子

      - [x] 点云网络Voxel划分体素方式计算基于上下文的积分特征

      - [x] 分组及采样，以一帧数据为例，点的划分由散列函数确定，划分依据是坐标（记录粒子序号（当然此序号不代表顺序，只是标示每一帧的每一个粒子）与划分体素对应关系）

           采用vexelnet的实现方式

      - [ ] 所有的voxel均已某个点的坐标作为中心可行吗，除了按照原网络结构提取全局特征，对于每一个流体粒子而言，以其坐标作为所有体素的中心坐标

           目前的问题是一个场景需要为每个粒子都划分一次网体空间，以该体素为基准，创建该粒子的

      - [ ] 结合voxelnet和pointnet，voxelnet进行数据的点特征的提取，pointnet进行全局特征的提取

- [ ] 流体仿真特性如何体现
      - [ ] 流固交互
      - [ ] 普通神经网络近似各项受力与加速度的关系

- [ ] 卷积网络
      - [ ] 共享的感知层为何可以转化为卷积运算
      - [ ] VFE层详解 本质上是pointnet，但mask部分尚有疑虑
      - [ ] 网络能够对逐点特征进行计算
      - [x] 不能套用网络结构，只是结合这种处理的思想，来计算粒子的邻居特征
           - [x] 不要再把tensor的shape当作张量本身了，strides=[1,2,2,1]这个它就是1D的张量而已，索引1，2代表h和w，0和3均为1且目前只能为1，以后可能会代表batch和特征图

- [ ] 模型训练及仿真整体实现
      - [ ] 模型结构、输入数据和标签、损失函数（及优化算法）

      - [ ] 结合voxelnet思考整个流程

           - [x] 仿真时，以流体粒子索引作为第二个参数，在驱动仿真时可以并行，根据索引提取相对坐标的中心值
           - [ ] 训练时，一帧数据应该按照单个流体粒子的坐标依次生成对应粒子的网体划分

      - [x] 固体粒子需要搜索邻居粒子 需要，因而固体粒子的时间不能省略

      - [ ] 修改模型结构，加载一个模型得到加速度，并以此加速度更新所有的流体粒子

           打通全流程的实验仿真，tensorflow使用c++调用python训练的模型。

           1. - [x] 使用python训练网络模型，存入checkpoint文件，之后使用freeze_graph.p将模型转存入ptotobuf文件
            2. - [ ] c++加载图及参数至session中，根据输入直接输出结果（但是目前对张量数据的加载仍未理解透彻，本来图片加载是一个很好的例子，目前仍需要继承三种方式，从array中直接加载，从csv中读取，从图片中提取）
            3. - [ ] 结合仿真程序加载模型并反馈网络的输出结果

      - [ ] GAN训练

      - [x] 矩阵乘法：

           np.dot():对于二维矩阵，计算真正意义上的矩阵乘积，同线性代数中矩阵乘法的定义。对于一维矩阵，计算两者的内积。

           np.multiply()张量的对应项相乘

- [ ] 典型网络算法解析

      - [x] Voxelnet包含三个层次

           特征学习层，卷积层，和rpn——为每一个粒子找到一个标识，进行其唯一特征提取，并通过卷积层进一步提取；最后进行回归，rpn似乎不可用，看看它到底是什么，再做一个实时目标检测的应用吧，逐层分解来看：

           - [ ] 特征表示层

               划分3D voxel网格(D' H' W') 每个体素的大小为（v_d,v_h,v_w）

               稀疏张量表示

               所有的voxel均已某个点的坐标作为中心可行吗，除了按照原网络结构提取全局特征，对于每一个流体粒子而言，以其坐标作为所有体素的中心坐标

            - [ ] cal_rpn_target

                  感兴趣区域池化(RoI Pooling)

                  区域建议网络（RegionProposal Network，RPN）

                  锚点最终是要映射回原始图片的尺寸

                  随机梯度下降的动量算法

      ​



将粒子根据坐标（全部转为正向坐标）将粒子划分入网体（voxel）内,feature shape(K, T， 7) K为当前粒子所能划分的网体数目，T为每个网体内最大的粒子容量，7为每个粒子编码的特征长度。

实际处理中是将网体按出现顺序编号，粒子已将以出现顺序编码在每个网体中。

训练中batch划分分为两个层次：

1. 首先对所有训练数据划分batch，每个batch将会有batch_size个文件
2. 根据GPU数目在每个batch内划分子batch，每个batch内的batch_size个文件将会被拼接，拼接的时候会在cordinate（标示网体位置的长度为3的一维元组）前添加不同文件的表识。

**VFE(Voxel Feature Encoding) layer**:

每个VFEdense全连接+max pooling

maxpoling的作用元素包括哪些呢？

FeatureNet mask

在FeatureNet之后，得到的是tf.scatter_nd根据batch和网体坐标生成的5-D全空间张量



损失函数
$$
L = α \cfrac{1}{N_{pos}}\sum_i L_{cls}(p^{pos}_i, 1) + β\cfrac1{N_{neg}}\sum_jL_{cls}(p_j^{neg}, 0)+ \cfrac1{N_{pos}}\sum_iL_{reg}(u_i,u^∗_i)
$$
$L_{cls}$表示二元交叉熵损失，$L_{reg}$表示光滑L1函数（只对分类为正的anchor进行计算）



肢解RPN

### 全流程仿真实验

在将训练模型存储为pb文件的过程中，需要明确得到网络的输出，在voxelnet中，对于划分到不同GPU下的不同参数，我最终应该选取哪一个，我又该如何快速的定位我所需要的输出变量

#### GAN模型试验

目前GAN模型很早就已实现在python环境下的存储和加载模型及生成结果，变量名的获取是关键

- [ ] c++将tensor保存为图片，查看效果，否则没有成果，无法形成激励
- [ ] 将c++的tensor api进行系统扩展应用是非常有必要的，因为这方面的资料实在是过于少，仅有的一些资料也显得特别初级和入门，没有实用性。
- [ ] 命名其实是一件很重要的事，你要区分命名是网络某一层的命名还是你最终得到的输出的命名。

#### 仿真模型

- [ ] 重点在于输入数据的处理，同时获取流体粒子和固体粒子，以流体粒子的索引作为该粒子的标识，**并行**进行网体划分（两个问题得到解决），同时带入模型得到输出

      - [x] 流体粒子数不同
      - [x] 不同粒子间无关联，可并行
      - [ ] 需要添加重力

- [ ] 所有粒子需要进入同一个Tensor中

- [ ] 将分组的代码以c++形式实现

      ​