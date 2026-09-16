# Campus Reference Reconstruction Benchmark

这个仓库用于测试 Agent 是否能够根据一个真实但拓扑混乱的 SketchUp 校园模型和航拍参考图，**重构一个新的、干净、结构化的校园 3D 场景**。

推荐在本机使用 **Blender + Blender MCP / Python** 完成。

> **禁止修复旧模型。旧模型只能作为只读三维 Reference。**

历史 repair submission 仅作为历史记录，不代表当前 benchmark 的有效提交。

## 输入与参考

### 1. 旧 SketchUp 模型

`input/6.8.6-颜色微调-1.skp`

原模型包含有价值的几何与空间关系，但内部拓扑非常混乱：

- 建筑、平台、桥、山体和地面可能直接粘连；
- 墙面不一定闭合；
- 裸线、裸面和错误连接较多；
- 对象缺少可靠的语义层级。

允许将其导入 / 转换到 Blender 中作为：

```text
REFERENCE_LOCKED
```

Reference 只用于观察、吸附、测量和几何对比。

**禁止直接编辑 Reference，也禁止通过清理、分离、重命名旧网格来冒充重构结果。**

### 2. 航拍参考图

![Campus zoning reference](references/campus_zoning_reference.jpg)

![Campus aerial reference](references/campus_aerial_reference.jpg)

参考图位于：

`references/`

用于交叉核对校园范围、建筑轮廓、道路、广场、运动场和整体布局。

## 核心目标

重构一个新的校园场景，同时满足：

- 尽可能保留原模型中的有效可见细节；
- 建筑、桥、平台、山体、道路等语义对象彼此独立；
- 保持原模型的全局坐标、尺寸、高程和空间关系；
- 不继承原模型的错误拓扑。

核心原则：

> **Preserve the design, not the broken topology.**

## 推荐结构

```text
Campus
├── Buildings
├── Bridges
├── Platforms
├── Terrain
├── Roads
├── Stairs
├── Sports
└── Details
```

不同建筑不要共享裸几何。

桥、平台、楼梯、山体等公共结构不要并入某一栋建筑。

## 工作流程

### 0. 建立 Reference

完整导入原模型，保持原始尺度、坐标和朝向，并锁定为 `REFERENCE_LOCKED`。

### 1. 建立全局骨架

先确认并固定关键空间关系：

- 建筑轮廓与主要标高；
- 平台关键点；
- 连桥两端；
- 楼梯上下端；
- 山体关键高程；
- 道路和主要公共空间。

这些位置是后续重构的全局锚点。

### 2. 原位重构

按区域逐步处理，但所有新对象必须直接在原始 XYZ 位置建立。

**禁止把各栋楼分别建完后，再通过移动、旋转或缩放手动拼齐。**

优先顺序：

1. 主体体量；
2. 桥、平台、楼梯和地形接口；
3. 门窗、栏杆、屋顶、装饰和材质。

### 3. 公共连接结构

平台、桥、楼梯、道路和山体必须作为独立对象重构。

特别注意：

- 平台不能因为连接某栋楼就归入该楼；
- 连桥两端必须落在正确的建筑 / 平台接口；
- 原模型中的真实坡度和高差必须保留；
- 不得擅自把看似倾斜的平台“优化”为水平。

### 4. 全局 QA

每完成一个区域，都应与 `REFERENCE_LOCKED` 叠加检查。

建议使用 Blender Python / MCP 自动检查：

- Bounding Box；
- 关键点 XYZ；
- 新旧表面距离；
- 接口高度；
- 非流形几何；
- 开放边界；
- 反法线；
- 孤立几何。

重点确认：

- 轮廓是否吻合；
- 高程是否一致；
- 平台是否意外倾斜；
- 桥两端是否准确连接；
- 建筑是否悬空或插入错误地形；
- 是否遗漏明显设计细节。

## 参考冲突时的优先级

1. **三维空间关系、高度、坡度、平台与连桥关系：原 SKP 优先；**
2. **平面轮廓、道路、建筑位置和整体布局：航拍图交叉核对；**
3. 彩色分区图仅用于识别校园范围和功能区。

不要机械复制原模型内部错误的面、边、Group 或组件结构。

## 禁止事项

- 禁止修复原模型并将其作为结果；
- 禁止直接编辑 `REFERENCE_LOCKED`；
- 禁止把原模型网格简单 Split / Clean / Separate 后作为新模型；
- 禁止各栋楼独立建模后最后手工拼接；
- 禁止为了简化任务而删除复杂连桥、平台或地形高差；
- 禁止只完成少量示例区域后宣称完成；
- 禁止直接向 `main` 提交 benchmark result。

## 交付方式

通过 Pull Request 提交。

主交付文件：

```text
submissions/<agent-name>/campus_recreated.blend
```

如环境能够可靠导出 SketchUp，可额外提交：

```text
submissions/<agent-name>/campus_recreated.skp
```

`.blend` 为当前 benchmark 的主模型。

PR 标题：

```text
[Submission] <agent-name> - campus reconstruction
```

PR 中说明：

- 使用的 Agent / 模型；
- Blender 版本与主要工具；
- 已重构内容；
- 已知偏差；
- 明确确认：**结果不是对旧 SKP 的修复或清理，而是在 Reference 基础上的新建重构。**

## 通过标准

一个有效提交至少应满足：

- `campus_recreated.blend` 能正常打开；
- 新模型与 Reference 几何相互独立；
- 主要校园建筑和空间关系完整；
- 连桥、平台、道路、山体和建筑高差没有明显错误；
- 整体布局与参考图一致；
- 主要三维关系与原 SKP 一致；
- 模型对象结构清晰并可继续编辑；
- 没有直接复用原模型的混乱拓扑作为主体。

当前 benchmark 的核心原则：

> **Reference globally. Reconstruct in place. Validate before moving on.**
