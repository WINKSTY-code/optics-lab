
/* =========================================================
 * V4.3 挑战模式 · 主入口
 * 模块清单：题库 / 绘图工具 / 几何兜底 / AI 判卷 / 高亮回显
 * ========================================================= */
(function(){
'use strict';

/* ===== 1. 题库（V4.9.6：5 道 → 11 道；type 支持 trace/pick/multi 三类） ===== */
const PROBLEMS = [
  {
    id:'reflect', type:'trace', name:'光的反射定律', diff:'basic', expKey:'reflect',
    scene:{ mirror:{x1:50,y1:400,x2:550,y2:400}, source:{x:100,y:100,label:'S'} },
    // 科学性核查：S(100,100)→O(400,400) 入射向量 (300,300)，与竖直法线夹角 = arctan(300/300) = 45° ✓
    std:{ incidentPoint:{x:400,y:400}, normalDir:{x:0,y:-1},
          incidentAngle:45, reflectionAngle:45, incidentColor:'#ef4444', reflectionColor:'#3b82f6' },
    criteria:['angle','keypoint','direction','normal_dashed'],
    criteriaWeight:{angle:40, keypoint:30, direction:20, normal_dashed:10},
    promptHint:'学生需画：入射光线（红）→法线（黑色虚线）→反射光线（蓝），并标注入射角 i=反射角 r=45°。'
  },
  {
    id:'mirror', type:'trace', name:'平面镜成像规律', diff:'basic', expKey:'mirror',
    // 科学性修正：改为竖直平面镜（苏科版标准场景）——像与物关于镜面左右对称、正立等大虚像
    scene:{ mirror:{x1:500,y1:80,x2:500,y2:420}, object:{x:300,y1:180,y2:280,label:'AB'} },
    std:{ imagePos:{x:700,y1:180,y2:280}, objectDistance:200, imageDistance:200,
          upright:true, virtual:true, label:"A'B'" },
    criteria:['symmetric','distance','upright','virtual_dashed'],
    criteriaWeight:{symmetric:40, distance:30, upright:20, virtual_dashed:10},
    promptHint:'学生需画：像 A\'B\' 与物关于竖直镜面左右对称（像距=物距=200px），正立等大虚像（虚线）。'
  },
  {
    id:'lens', type:'trace', name:'凸透镜成像（u>2f）', diff:'mid', expKey:'lens',
    // 科学性修正：主光轴 y=300；蜡烛底(200,300) 顶(200,200) 高100；u=260；v=1/(1/80-1/260)=115.6
    // 像在凸透镜另一侧 x=576（介于 F\'540 与 2F\'620 之间），倒立缩小实像高 44.4
    scene:{ lens:{x:460}, f:80, axis:{y:300}, object:{x:200,y1:300,y2:200,label:'蜡烛'} },
    std:{ imagePos:{x:576,y1:300,y2:344}, v:115.6, ratio:0.44,
          inverted:true, real:true },
    criteria:['imageInF2F','inverted','real_solid','ratio'],
    criteriaWeight:{imageInF2F:40, inverted:25, real_solid:20, ratio:15},
    promptHint:'物距 u=260>2f=160，像应在凸透镜另一侧 f<v<2f 区间（80<v<160），成倒立缩小实像。'
  },
  {
    id:'refract', type:'trace', name:'光的折射（空气→水）', diff:'mid', expKey:'refract',
    // 科学性修正：入射点 O(400,300)，入射向量 (153,129)，入射角 = arctan(153/129) = 50.0° ✓
    // 折射角 = arcsin(sin50°/1.33) = 35.2°（原 35.5° 不准）
    scene:{ interface:{y:300}, upper:'air', lower:'water', n:1.33,
            incident:{from:{x:247,y:171}, to:{x:400,y:300}, label:'入射'} },
    std:{ refractionAngle:35.2, incidentAngle:50, refractColor:'#10b981',
          normalsBoth:true },
    criteria:['refractAngle','refractColor','normalBoth','incident'],
    criteriaWeight:{refractAngle:40, refractColor:20, normalBoth:25, incident:15},
    promptHint:'入射角 50°，从空气射入水（n=1.33），折射角≈35.2°，折射光线偏向法线（画在水中）。'
  },
  {
    id:'disperse', type:'trace', name:'光的色散', diff:'adv', expKey:'disperse',
    scene:{ prism:{cx:460, cy:260, w:120, h:200}, whiteIn:{from:{x:100,y:260}, to:{x:400,y:260}} },
    std:{ colors:['#ef4444','#f97316','#eab308','#22c55e','#3b82f6','#6366f1','#a855f7'],
          order:'红橙黄绿蓝靛紫', redTop:true, violetBottom:true },
    criteria:['colorCount','colorOrder','redTop','violetBottom'],
    criteriaWeight:{colorCount:25, colorOrder:30, redTop:25, violetBottom:20},
    promptHint:'白光经三棱镜分解为 7 色，红光偏折最小在上，紫光偏折最大在下。'
  },
  /* ---- V4.9.6：以下 6 题为新增（trace×3 + pick×3），覆盖 7 个之前挑战不到的知识点 ---- */
  {
    id:'line-hole', type:'trace', name:'光的直线传播（小孔成像）', diff:'basic', expKey:'line',
    // V4.9.8 科学性核查（修正）：
    //   物：x=180，高 200（y1=140 顶 / y2=340 底）；小孔：x=460, y=240；屏：x=740
    //   物距 = 460-180 = 280；像距 = 740-460 = 280 → 像距=物距 ⇒ 像与物等大（高 200）
    //   物顶(y=140) 的光过孔后落在屏 y=340；物底(y=340) 的光落在屏 y=140 ⇒ 上下颠倒
    //   注意 imagePos.y1/y2 全站统一为"y1=像的上端、y2=像的下端"，
    //   本像倒立，故 y1=140（对应物底的光）、y2=340（对应物顶的光）
    //   旧版参数（屏 x=560 / imagePos 160~360 / ratio:1.0）经核算像高仅 71.4，与"等大"矛盾，已弃用
    scene:{ object:{x:180,y1:140,y2:340,label:''}, hole:{x:460,y:240,size:4},
            screen:{x:740,y1:80,y2:400} },
    std:{ imagePos:{x:740,y1:140,y2:340}, inverted:true, real:true,
          label:'↑（倒立）', ratio:1.0, holeDistance:280 },
    criteria:['inverted','symmetric','real_solid','ratio'],
    criteriaWeight:{inverted:35, symmetric:35, real_solid:15, ratio:15},
    promptHint:'小孔成像特点：像与物等大、上下左右颠倒、光屏可承接（实像）。本题物距=像距，物体高 200，画出倒立等大的像。'
  },
  {
    id:'lens-virtual', type:'trace', name:'凸透镜成像（u<f 虚像）', diff:'mid', expKey:'lens',
    // 科学性核查：f=80, u=60<f。虚像：v=-240（与物同侧），放大率 m=f/(f-u)=4
    // 透镜在 x=460，物体在 x=400，u=60。虚像位置 x=460-240=220（与物同侧，介于物体和透镜之间）
    // V4.9.10 修正：原物体高 100 ⇒ 像高 400 ⇒ 像顶 y=300-400=-100，**整个像跑到画布外面**
    //   学生开「查看标准答案」什么也看不见。现把物体高改为 60（底在主轴 y=300、顶 y=240），
    //   像高 = 60×4 = 240 ⇒ 像顶 y=300-240=60，完整落在 520 高的画布内。
    //   放大率 4 与题干口径不变，只是把"参照物"调小，让图能画得下。
    scene:{ lens:{x:460}, f:80, axis:{y:300}, object:{x:400,y1:300,y2:240,label:'蜡烛'} },
    std:{ imagePos:{x:220,y1:300,y2:60}, v:-240, ratio:4,
          inverted:false, real:false, virtual:true,
          sameSideAsObject:true },
    criteria:['sameSide','upright','virtual_dashed','ratio'],
    criteriaWeight:{sameSide:35, upright:25, virtual_dashed:25, ratio:15},
    promptHint:'u=60<f=80 时，凸透镜成正立放大虚像，像与物在透镜同侧（虚线）。'
  },
  {
    id:'refract-glass', type:'pick', name:'光的折射（光从玻璃射向空气）', diff:'mid', expKey:'refract',
    // V4.9.8：① 改为单选（原为多选，用户要求全单选）
    //         ② 题干与选项已剔除 n 值与公式（苏科版八年级不涉及该内容）
    question:'光从玻璃斜射入空气中时，折射角与入射角的大小关系是？',
    options:[
      { id:'A', text:'折射角等于入射角', correct:false,
        explain:'折射角一般不等于入射角；只有垂直入射（入射角为 0）时光线方向才不变' },
      { id:'B', text:'折射角小于入射角', correct:false,
        explain:'这是光从空气斜射入玻璃（光疏→光密）时的情形，方向反了' },
      { id:'C', text:'折射角大于入射角', correct:true,
        explain:'✓ 光从玻璃斜射入空气，折射光线偏离法线，折射角大于入射角' },
      { id:'D', text:'无法判断，与入射角无关', correct:false,
        explain:'折射角随入射角变化，二者有确定的对应关系，不是无关' }
    ],
    criteria:['answer'],
    criteriaWeight:{answer:100},
    promptHint:'玻璃和空气相比，哪种介质更"密"？光从这个介质射向另一种时，折射光线是靠近还是偏离法线？'
  },
  {
    id:'lens-converge', type:'pick', name:'透镜对光线的作用', diff:'basic', expKey:'lensfx',
    question:'凸透镜对平行于主光轴的光线的作用是？',
    options:[
      { id:'A', text:'会聚到焦点 F', correct:true, explain:'✓ 凸透镜使平行光会聚于焦点' },
      { id:'B', text:'发散（反向延长过虚焦点）', correct:false, explain:'这是凹透镜的特点' },
      { id:'C', text:'保持平行射出', correct:false, explain:'平面镜才有此特性' },
      { id:'D', text:'方向完全不变', correct:false, explain:'透镜会改变光线方向' }
    ],
    criteria:['answer'],
    criteriaWeight:{answer:100},
    promptHint:'凸透镜中间厚、边缘薄，对光有会聚作用。想想老花镜的原理。'
  },
  {
    id:'three-rays', type:'pick', name:'三条特殊光线（识别）', diff:'basic', expKey:'lensfx',
    question:'过光心的光线经过凸透镜后会：',
    options:[
      { id:'A', text:'方向不变', correct:true, explain:'✓ 光心处透镜薄到可视为平行玻璃砖，仅侧移可忽略' },
      { id:'B', text:'会聚到焦点', correct:false, explain:'这是平行主光轴的光线' },
      { id:'C', text:'变为平行光射出', correct:false, explain:'这是过焦点的光线（光路可逆）' },
      { id:'D', text:'反射回光源', correct:false, explain:'不发生反射，光线仍向前折射' }
    ],
    criteria:['answer'],
    criteriaWeight:{answer:100},
    promptHint:'想想光心处的透镜厚度特点（极薄，近似平行玻璃砖）'
  },
  {
    id:'ir-uv-app', type:'pick', name:'红外线与紫外线（应用）', diff:'basic', expKey:'eye',
    // V4.9.8：改为单选（原为多选，用户要求全单选）——只保留唯一正确答案
    question:'下列应用中，利用紫外线的是？',
    options:[
      { id:'A', text:'银行验钞机（让荧光物质发光）', correct:true, explain:'✓ 验钞机利用紫外线的荧光效应，属紫外线应用' },
      { id:'B', text:'电视遥控器', correct:false, explain:'遥控器用的是红外线（红外遥控），不是紫外线' },
      { id:'C', text:'浴室取暖器', correct:false, explain:'取暖器用红外线的热效应，不是紫外线' },
      { id:'D', text:'微波炉加热食物', correct:false, explain:'微波炉用微波（电磁波的一种），既不是红外线也不是紫外线' }
    ],
    criteria:['answer'],
    criteriaWeight:{answer:100},
    promptHint:'紫外线有荧光效应和化学效应（能杀菌、能让荧光物质发光）；红外线主要是热效应。'
  },

  /* ===== V4.10.0 新增选择题（32 道，逐题核验科学性与唯一答案） ===== */
  { id:'q-light-source', type:'pick', name:'光源的判断', diff:'basic', expKey:'reflect',
    question:'下列物体中，属于光源的是？',
    options:[
      { id:'A', text:'太阳', correct:true, explain:'✓ 自身能发光的物体叫光源，太阳自身发光，是（天然）光源' },
      { id:'B', text:'月亮', correct:false, explain:'月亮自身不发光，我们看到的月光是它反射的太阳光' },
      { id:'C', text:'平面镜', correct:false, explain:'平面镜只能反射光，自身不发光' },
      { id:'D', text:'白纸', correct:false, explain:'白纸反射光进入眼睛才被看见，自身不发光' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'关键看物体是"自己发光"还是"反射别人的光"。'
  },
  { id:'q-light-speed', type:'pick', name:'光在真空中的速度', diff:'basic', expKey:'line',
    question:'光在真空中的传播速度约为？',
    options:[
      { id:'A', text:'3×10⁸ m/s', correct:true, explain:'✓ 真空中光速 c≈3×10⁸ m/s，是自然界最快的速度' },
      { id:'B', text:'3×10⁶ m/s', correct:false, explain:'数量级不对，真空中光速是 3×10⁸ m/s' },
      { id:'C', text:'340 m/s', correct:false, explain:'340 m/s 是声音在 15℃ 空气中的速度' },
      { id:'D', text:'1.5×10⁸ m/s', correct:false, explain:'光从真空进入介质速度会变小，但真空中是 3×10⁸ m/s' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'注意区分"光速"与"声速"，二者数量级差很大。'
  },
  { id:'q-light-prop', type:'pick', name:'光的传播（说法辨析）', diff:'basic', expKey:'line',
    question:'关于光的传播，下列说法正确的是？',
    options:[
      { id:'A', text:'光在同种均匀介质中沿直线传播', correct:true, explain:'✓ 这是光的直线传播的成立条件：同种、均匀介质' },
      { id:'B', text:'光的传播必须依赖介质', correct:false, explain:'光的传播不需要介质，在真空中也能传播（声音才需要介质）' },
      { id:'C', text:'光在任何介质中的速度都是 3×10⁸ m/s', correct:false, explain:'3×10⁸ m/s 是真空中的光速，在介质中光速会变小' },
      { id:'D', text:'光在任何情况下都沿直线传播', correct:false, explain:'介质不均匀时光线会弯曲，如"海市蜃楼"现象' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'注意"同种、均匀"这两个前提条件缺一不可。'
  },
  { id:'q-shadow', type:'pick', name:'影子的成因', diff:'basic', expKey:'line',
    question:'光射到不透明物体上，在物体后面形成影子，其成因是？',
    options:[
      { id:'A', text:'光的直线传播', correct:true, explain:'✓ 光沿直线传播，遇到不透明物体被挡住，后面形成影子' },
      { id:'B', text:'光的反射', correct:false, explain:'反射是光遇到物体表面返回，与影子的形成无关' },
      { id:'C', text:'光的折射', correct:false, explain:'折射是光进入另一种介质时方向偏折，不是影子成因' },
      { id:'D', text:'光的色散', correct:false, explain:'色散是复色光分解为单色光，与影子无关' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'影子、日食、月食、小孔成像都是同一类成因。'
  },
  { id:'q-eclipse', type:'pick', name:'日食的成因', diff:'basic', expKey:'line',
    question:'日食发生时，挡住太阳射向地球的光的 天体 与成因分别是？',
    options:[
      { id:'A', text:'月球挡住太阳光，由光的直线传播形成', correct:true, explain:'✓ 月球运行到太阳和地球之间，光沿直线传播被月球挡住' },
      { id:'B', text:'地球挡住太阳光，由光的直线传播形成', correct:false, explain:'地球挡住太阳光是月食，不是日食' },
      { id:'C', text:'月球挡住太阳光，由光的反射形成', correct:false, explain:'成因是光的直线传播，不是反射' },
      { id:'D', text:'金星挡住太阳光，由光的折射形成', correct:false, explain:'日食是月球挡住的，且与折射无关' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'记住顺序：日月地在一条直线上，月球在中间是日食，地球在中间是月食。'
  },
  { id:'q-pinhole-fact', type:'pick', name:'小孔成像的特点', diff:'basic', expKey:'line',
    question:'关于小孔成像，下列说法正确的是？',
    options:[
      { id:'A', text:'所成的像是倒立的实像', correct:true, explain:'✓ 光沿直线传播，光屏上能得到倒立的实像' },
      { id:'B', text:'所成的像是正立的虚像', correct:false, explain:'小孔成像成的是倒立的实像，能用光屏承接' },
      { id:'C', text:'像的形状由小孔的形状决定', correct:false, explain:'像的形状由物体决定，与孔形状无关（孔要足够小）' },
      { id:'D', text:'像一定比物体小', correct:false, explain:'像可大可小，取决于屏到孔的距离与物到孔的距离之比' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'小孔成像的像"倒立、实像、形状看物体、大小看距离"。'
  },
  { id:'q-align', type:'pick', name:'直线传播的应用', diff:'basic', expKey:'line',
    question:'射击瞄准时要做到"三点一线"（缺口、准星、目标），利用的原理是？',
    options:[
      { id:'A', text:'光的直线传播', correct:true, explain:'✓ 光在空气中沿直线传播，三点成一线即可命中' },
      { id:'B', text:'光的反射', correct:false, explain:'瞄准不涉及光的反射' },
      { id:'C', text:'光的折射', correct:false, explain:'瞄准不涉及光的折射' },
      { id:'D', text:'光的色散', correct:false, explain:'色散与瞄准无关' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'同类的还有激光准直、排队看齐、植树成行。'
  },
  { id:'q-refl-angle', type:'pick', name:'反射角的大小', diff:'basic', expKey:'reflect',
    question:'一束光射到平面镜上，入射光线与镜面的夹角为 30°，则反射角为？',
    options:[
      { id:'A', text:'60°', correct:true, explain:'✓ 入射角 = 90° − 30° = 60°（入射光线与法线的夹角），反射角 = 入射角 = 60°' },
      { id:'B', text:'30°', correct:false, explain:'30° 是入射光线与镜面的夹角，入射角应是与法线的夹角' },
      { id:'C', text:'90°', correct:false, explain:'90° 是入射光线与镜面垂直时的情形' },
      { id:'D', text:'0°', correct:false, explain:'0° 对应垂直入射的情形' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'先分清"与镜面的夹角"和"与法线的夹角"，入射角是后者。'
  },
  { id:'q-angle-def', type:'pick', name:'入射角的定义', diff:'basic', expKey:'reflect',
    question:'在光的反射现象中，"入射角"是指入射光线与下列哪条线之间的夹角？',
    options:[
      { id:'A', text:'入射光线与法线的夹角', correct:true, explain:'✓ 入射角、反射角都是与"法线"的夹角，不是与镜面的夹角' },
      { id:'B', text:'入射光线与镜面的夹角', correct:false, explain:'与镜面的夹角 ≠ 入射角，二者互余' },
      { id:'C', text:'入射光线与反射光线的夹角', correct:false, explain:'这是两光线之间的夹角，不是入射角' },
      { id:'D', text:'反射光线与法线的夹角', correct:false, explain:'这是反射角的定义' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'"角"的定义永远是跟法线比，别跟镜面比。'
  },
  { id:'q-refl-reversible', type:'pick', name:'反射时光路可逆', diff:'basic', expKey:'reflect',
    question:'让光逆着原来反射光线的方向射到平面镜上，反射光线将：',
    options:[
      { id:'A', text:'逆着原来入射光线的方向射出', correct:true, explain:'✓ 反射时光路可逆，沿原路返回' },
      { id:'B', text:'沿原来的反射方向继续射出', correct:false, explain:'光路可逆意味着反过来照，光就沿原入射方向返回' },
      { id:'C', text:'发生折射进入镜子里', correct:false, explain:'平面镜不透光，不发生折射' },
      { id:'D', text:'无法确定方向', correct:false, explain:'反射定律是确定的，光路可逆也是确定的' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'"光路可逆"在反射和折射中都成立。'
  },
  { id:'q-diffuse', type:'pick', name:'镜面反射与漫反射', diff:'mid', expKey:'reflect',
    question:'关于镜面反射和漫反射，下列说法正确的是？',
    options:[
      { id:'A', text:'两者都遵循光的反射定律', correct:true, explain:'✓ 每条光线都遵守反射定律，漫反射只因反射面凹凸不平，法线方向各不相同' },
      { id:'B', text:'只有镜面反射遵循反射定律', correct:false, explain:'漫反射同样遵循反射定律' },
      { id:'C', text:'漫反射中反射角不等于入射角', correct:false, explain:'对每一条光线来说，反射角都等于入射角' },
      { id:'D', text:'只有镜面反射时光路可逆', correct:false, explain:'两类反射都满足光路可逆' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'黑板"反光"是镜面反射，各个方向都能看到银幕是漫反射。'
  },
  { id:'q-mirror-size', type:'pick', name:'平面镜成像（像的大小）', diff:'basic', expKey:'mirror',
    question:'人走近平面镜时，他在镜中的像的大小将：',
    options:[
      { id:'A', text:'不变，始终与人的大小相等', correct:true, explain:'✓ 平面镜成等大的像，像的大小只由人自身大小决定' },
      { id:'B', text:'变大', correct:false, explain:'"看起来变大"是视角变大的错觉，像的实际大小不变' },
      { id:'C', text:'变小', correct:false, explain:'同上，像的大小与距离无关' },
      { id:'D', text:'先变大后变小', correct:false, explain:'像的大小始终与人相等，不随距离变化' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'平面镜成像特点：等大、正立、虚像、像物到镜面距离相等。'
  },
  { id:'q-mirror-principle', type:'pick', name:'平面镜成像的原理', diff:'basic', expKey:'mirror',
    question:'平面镜成像的原理是？',
    options:[
      { id:'A', text:'光的反射', correct:true, explain:'✓ 像是由反射光线的反向延长线会聚而成的虚像，原理是光的反射' },
      { id:'B', text:'光的折射', correct:false, explain:'折射是光进入另一种介质发生的现象，平面镜成像不是' },
      { id:'C', text:'光的直线传播', correct:false, explain:'直线传播对应影子、日食、小孔成像等' },
      { id:'D', text:'光的色散', correct:false, explain:'色散是白光分解为七色光，与成像原理无关' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'虚像 = 反射光线的反向延长线"会聚"，不是实际光线会聚。'
  },
  { id:'q-lake-image', type:'pick', name:'水中的"倒影"', diff:'basic', expKey:'mirror',
    question:'岸边树木在平静湖水中的"倒影"，下列说法正确的是？',
    options:[
      { id:'A', text:'是等大的虚像，由光的反射形成', correct:true, explain:'✓ 平静水面相当于平面镜，成等大、正立的虚像' },
      { id:'B', text:'是等大的实像，由光的折射形成', correct:false, explain:'倒影是虚像，且成因是反射不是折射' },
      { id:'C', text:'是缩小的虚像，由光的反射形成', correct:false, explain:'平面镜成等大的像，不会缩小' },
      { id:'D', text:'是影子，由光的直线传播形成', correct:false, explain:'倒影是成像现象，不是影子' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'平静的水面、抛光的金属面都可以看作平面镜。'
  },
  { id:'q-chopstick', type:'pick', name:'折射现象的识别', diff:'basic', expKey:'refract',
    question:'插入水中的筷子看起来在水面处向上弯折，这是光的：',
    options:[
      { id:'A', text:'折射现象', correct:true, explain:'✓ 光从水斜射入空气时方向偏折，看到的"水中部分"是变浅的虚像' },
      { id:'B', text:'反射现象', correct:false, explain:'反射不解释筷子"弯折"，这是光进入空气时发生折射' },
      { id:'C', text:'直线传播现象', correct:false, explain:'若光沿直线传播，筷子看起来不会弯折' },
      { id:'D', text:'色散现象', correct:false, explain:'色散是白光分解成彩色光带，与弯折无关' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'同类现象：水中的鱼看起来变浅、海市蜃楼、透过水滴看字放大。'
  },
  { id:'q-refract-law', type:'pick', name:'折射角的比较', diff:'basic', expKey:'refract',
    question:'光从空气中斜射入水中时，折射角与入射角的关系是？',
    options:[
      { id:'A', text:'折射角小于入射角', correct:true, explain:'✓ 光从空气（光疏介质）斜射入水（光密介质），折射光线靠近法线' },
      { id:'B', text:'折射角大于入射角', correct:false, explain:'这是光从水斜射入空气时的情形' },
      { id:'C', text:'折射角等于入射角', correct:false, explain:'只有垂直入射（入射角为 0°）时才相等' },
      { id:'D', text:'折射角为 90°', correct:false, explain:'90° 是恰好发生全反射的临界情形，苏科版阶段不作要求' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'口诀：空气中的角总是"大"的那一个（斜射时）。'
  },
  { id:'q-normal-incident', type:'pick', name:'垂直入射的情形', diff:'basic', expKey:'refract',
    question:'一束光垂直射向水面，进入水中时它的传播方向：',
    options:[
      { id:'A', text:'不变，折射角为 0°', correct:true, explain:'✓ 垂直入射时光线沿原方向进入水中，传播方向不变' },
      { id:'B', text:'偏向法线，折射角大于 0°', correct:false, explain:'斜射时才会偏折，垂直入射方向不变' },
      { id:'C', text:'全部被反射回空气中', correct:false, explain:'垂直入射时光仍会进入水中' },
      { id:'D', text:'发生色散分解为七色光', correct:false, explain:'色散发生在斜射入三棱镜等情形，与垂直入射无关' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'垂直入射是折射中的特殊情况：入射角 = 折射角 = 0°。'
  },
  { id:'q-fish-spearing', type:'pick', name:'叉鱼要瞄"下方"', diff:'mid', expKey:'refract',
    question:'渔民叉鱼时，要瞄准看到的鱼的下方才能叉到，这是因为：',
    options:[
      { id:'A', text:'看到的是光的折射形成的虚像，鱼的实际位置比看到的深', correct:true,
        explain:'✓ 鱼反射的光从水射入空气发生折射，人看到的是变浅了的虚像' },
      { id:'B', text:'看到的就是鱼的实际位置，只是要瞄低些', correct:false, explain:'若看到的就是实际位置，直接叉就行了' },
      { id:'C', text:'鱼反射的光沿直线传播进入人眼', correct:false, explain:'光从水到空气发生了折射，不是直线传播' },
      { id:'D', text:'水面相当于平面镜，鱼在镜中成放大的像', correct:false, explain:'这属于折射成像，不是平面镜成像' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'从空气看水中的物体：看到的虚像比实际位置浅。'
  },
  { id:'q-concave-lens', type:'pick', name:'凹透镜对光的作用', diff:'basic', expKey:'lensfx',
    question:'凹透镜对光线的作用是？',
    options:[
      { id:'A', text:'发散作用', correct:true, explain:'✓ 凹透镜中间薄、边缘厚，对光有发散作用' },
      { id:'B', text:'会聚作用', correct:false, explain:'会聚是凸透镜的作用' },
      { id:'C', text:'既不会聚也不发散', correct:false, explain:'除垂直入射的光轴方向外，经过凹透镜的光线都会发散' },
      { id:'D', text:'只对彩色光有发散作用', correct:false, explain:'凹透镜对所有光的发散作用与颜色无关' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'近视眼镜的镜片就是凹透镜。'
  },
  { id:'q-focal-length', type:'pick', name:'测凸透镜的焦距', diff:'basic', expKey:'lensfx',
    question:'让平行于主光轴的光射向凸透镜，光屏上得到一个最小最亮的光斑，光斑到光心的距离为 10 cm，则该透镜的焦距为？',
    options:[
      { id:'A', text:'10 cm', correct:true, explain:'✓ 平行主光轴的光会聚于焦点，焦点到光心的距离就是焦距' },
      { id:'B', text:'5 cm', correct:false, explain:'光斑到光心的距离就是焦距，不需要再除以 2' },
      { id:'C', text:'20 cm', correct:false, explain:'焦距是焦点到光心的距离，不是两倍' },
      { id:'D', text:'无法确定', correct:false, explain:'题目信息已足够确定焦距' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'"最小最亮的光斑"就是焦点，这是粗测焦距的标准方法。'
  },
  { id:'q-camera', type:'pick', name:'照相机的成像', diff:'basic', expKey:'lens',
    question:'照相机拍摄景物时，物体到镜头的距离（物距）满足：',
    options:[
      { id:'A', text:'大于二倍焦距，成倒立缩小的实像', correct:true, explain:'✓ u＞2f 时，凸透镜成倒立、缩小的实像，落在光屏（底片）上' },
      { id:'B', text:'小于一倍焦距，成正立放大的虚像', correct:false, explain:'这是放大镜的情形' },
      { id:'C', text:'等于二倍焦距，成等大的像', correct:false, explain:'u＝2f 成等大实像，不是照相机的通常工作区间' },
      { id:'D', text:'在一倍焦距和二倍焦距之间，成放大的像', correct:false, explain:'这是投影仪（幻灯机）的情形' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'照相机：物远像近像变小（u＞2f）。'
  },
  { id:'q-u2f', type:'pick', name:'u = 2f 时的成像', diff:'mid', expKey:'lens',
    question:'物体放在距凸透镜二倍焦距处（u = 2f），所成的像是：',
    options:[
      { id:'A', text:'倒立、等大的实像', correct:true, explain:'✓ u＝2f 是成放大像与缩小像的分界点，像与物等大、倒立、实像' },
      { id:'B', text:'倒立、缩小的实像', correct:false, explain:'缩小实像对应 u＞2f' },
      { id:'C', text:'正立、放大的虚像', correct:false, explain:'虚像对应 u＜f' },
      { id:'D', text:'不成像', correct:false, explain:'u＝f（焦点处）才不成像，u＝2f 能成清晰等大的像' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'记住分界点：u＝2f 分"缩小/放大"，u＝f 分"实像/虚像"。'
  },
  { id:'q-projector', type:'pick', name:'投影仪的成像', diff:'basic', expKey:'lens',
    question:'投影仪（幻灯机）工作时，胶片到镜头的距离应满足：',
    options:[
      { id:'A', text:'大于一倍焦距、小于二倍焦距，成倒立放大的实像', correct:true,
        explain:'✓ f＜u＜2f 时成倒立、放大的实像，投到远处的屏幕上' },
      { id:'B', text:'大于二倍焦距，成缩小的实像', correct:false, explain:'这是照相机的情形' },
      { id:'C', text:'小于一倍焦距，成放大的虚像', correct:false, explain:'这是放大镜的情形，虚像无法投到屏幕上' },
      { id:'D', text:'等于二倍焦距，成等大的实像', correct:false, explain:'等大像无法让屏幕上的画面放大' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'投影仪：物近像远像变大（f＜u＜2f）。'
  },
  { id:'q-magnifier', type:'pick', name:'放大镜的成像', diff:'basic', expKey:'lens',
    question:'用放大镜观察邮票时，看到的是：',
    options:[
      { id:'A', text:'正立、放大的虚像', correct:true, explain:'✓ 邮票在一倍焦距以内，凸透镜成正立、放大的虚像' },
      { id:'B', text:'倒立、放大的实像', correct:false, explain:'实像要用光屏承接，且是倒立的，与放大镜看到的不符' },
      { id:'C', text:'倒立、等大的实像', correct:false, explain:'等大实像对应 u＝2f' },
      { id:'D', text:'正立、缩小的虚像', correct:false, explain:'凸透镜不能成正立缩小的像（凹透镜才行）' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'放大镜 = u＜f 时的凸透镜成像。'
  },
  { id:'q-real-virtual', type:'pick', name:'实像与虚像的区别', diff:'mid', expKey:'lens',
    question:'关于实像和虚像，下列说法正确的是？',
    options:[
      { id:'A', text:'实像由实际光线会聚而成，能用光屏承接', correct:true,
        explain:'✓ 这是实像的本质特征；虚像只能用眼睛看到，不能用光屏承接' },
      { id:'B', text:'虚像不能用眼睛直接看到', correct:false, explain:'虚像恰恰是用人眼看到的，只是不能呈现在光屏上' },
      { id:'C', text:'平面镜成的是实像', correct:false, explain:'平面镜成的是虚像' },
      { id:'D', text:'凸透镜只能成实像', correct:false, explain:'u＜f 时凸透镜成虚像（放大镜）' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'一句话区分：能不能用光屏接到——能是实，不能是虚。'
  },
  { id:'q-myopia', type:'pick', name:'近视眼的矫正', diff:'basic', expKey:'eye',
    question:'关于近视眼及其矫正，下列说法正确的是？',
    options:[
      { id:'A', text:'像成在视网膜前方，需要佩戴凹透镜矫正', correct:true,
        explain:'✓ 近视眼晶状体太厚（或眼球太长），折光太强，像落在视网膜前方；凹透镜先发散一下，像后移到视网膜上' },
      { id:'B', text:'像成在视网膜后方，需要佩戴凸透镜矫正', correct:false, explain:'这是远视眼的特点和矫正方法' },
      { id:'C', text:'像成在视网膜前方，需要佩戴凸透镜矫正', correct:false, explain:'位置说对了但镜片错了，凸透镜会让像更靠前' },
      { id:'D', text:'像成在视网膜后方，需要佩戴凹透镜矫正', correct:false, explain:'位置和镜片都说反了' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'近视："前方 + 凹透镜"；远视："后方 + 凸透镜"。'
  },
  { id:'q-hyperopia', type:'pick', name:'远视眼（老花眼）的矫正', diff:'basic', expKey:'eye',
    question:'远视眼看近处物体时，像成在视网膜的：',
    options:[
      { id:'A', text:'后方，应佩戴凸透镜制成的眼镜', correct:true,
        explain:'✓ 远视眼折光偏弱，像落在视网膜后方，凸透镜的会聚作用让像前移到视网膜上' },
      { id:'B', text:'前方，应佩戴凹透镜制成的眼镜', correct:false, explain:'这是近视眼的情形' },
      { id:'C', text:'后方，应佩戴凹透镜制成的眼镜', correct:false, explain:'位置对但镜片错，凹透镜会让像更靠后' },
      { id:'D', text:'正中央，无需矫正', correct:false, explain:'看不清近处物体才叫远视，说明像没有落在视网膜上' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'老花镜片中间厚边缘薄，是凸透镜。'
  },
  { id:'q-dispersion', type:'pick', name:'光的色散', diff:'basic', expKey:'disperse',
    question:'太阳光通过三棱镜后，在白屏上形成红、橙、黄、绿、蓝、靛、紫的彩色光带，这说明：',
    options:[
      { id:'A', text:'白光是由多种色光混合而成的复色光', correct:true, explain:'✓ 这就是光的色散实验（牛顿），白光可分解为七种单色光' },
      { id:'B', text:'三棱镜能产生彩色光', correct:false, explain:'彩色光不是三棱镜"造"出来的，是把白光中本来的成分分开了' },
      { id:'C', text:'白光是单色光', correct:false, explain:'白光由七色光混合而成，是复色光' },
      { id:'D', text:'彩色光带是光屏反射形成的', correct:false, explain:'色带的成因是折射程度不同导致的色散，不是反射' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'1666 年牛顿的三棱镜色散实验。'
  },
  { id:'q-color-filter', type:'pick', name:'透明物体的颜色', diff:'mid', expKey:'disperse',
    question:'透过红色透明玻璃看白纸，白纸呈现的颜色是？',
    options:[
      { id:'A', text:'红色', correct:true, explain:'✓ 红色玻璃只透过红光；白纸反射所有色光，其中只有红光能透过玻璃进入眼睛' },
      { id:'B', text:'白色', correct:false, explain:'七色光中只有红光透过了玻璃，不可能仍是白色' },
      { id:'C', text:'黑色', correct:false, explain:'若白纸不反射红光才是黑色；白纸反射所有色光，包括红光' },
      { id:'D', text:'绿色', correct:false, explain:'绿光被红色玻璃吸收，透不过来' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'透明物体的颜色由"透过的色光"决定；不透明物体由"反射的色光"决定。'
  },
  { id:'q-ir-app', type:'pick', name:'红外线的应用', diff:'basic', expKey:'eye',
    question:'下列设备中，利用红外线工作的是？',
    options:[
      { id:'A', text:'电视遥控器', correct:true, explain:'✓ 家电遥控器利用红外线脉冲传递信号' },
      { id:'B', text:'验钞机', correct:false, explain:'验钞机利用的是紫外线的荧光效应' },
      { id:'C', text:'杀菌灯', correct:false, explain:'杀菌利用的是紫外线的化学作用' },
      { id:'D', text:'三棱镜分光镜', correct:false, explain:'三棱镜利用折射做色散实验，与红外线应用无关' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'红外线：热效应强（取暖、遥控、夜视仪）；紫外线：荧光效应、杀菌。'
  },
  { id:'q-light-year', type:'pick', name:'"光年"是什么单位', diff:'basic', expKey:'line',
    question:'天文学中常用"光年"来计量，光年是：',
    options:[
      { id:'A', text:'长度单位，即光在一年中通过的距离', correct:true,
        explain:'✓ 光年是距离（长度）单位，约 9.46×10¹² km' },
      { id:'B', text:'时间单位，即光走一年所花的时间', correct:false, explain:'光年量的是"距离"，不是时间' },
      { id:'C', text:'速度单位', correct:false, explain:'速度单位是 m/s 这类，光年不是' },
      { id:'D', text:'光的亮度单位', correct:false, explain:'描述光强有专门单位，光年与其无关' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'别被"年"字骗了——光年是"光跑一年的路程"。'
  },
  { id:'q-refract-reversible', type:'pick', name:'折射时光路可逆', diff:'mid', expKey:'refract',
    question:'光从空气斜射入水中，入射角为 60° 时折射角为 40°。若光从水中沿原来折射光线的反方向射入空气，此时的折射角为？',
    options:[
      { id:'A', text:'60°', correct:true, explain:'✓ 折射时光路可逆：水中入射角 40°，进入空气后折射角为 60°，沿原入射方向射出' },
      { id:'B', text:'40°', correct:false, explain:'40° 是水中的入射角；进入空气后折射角应变大' },
      { id:'C', text:'30°', correct:false, explain:'与光路可逆规律不符' },
      { id:'D', text:'90°', correct:false, explain:'90° 不是这里的折射角' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'光路可逆：反着照，就反着回，角度一一对应。'
  },
  { id:'q-light-pollution', type:'pick', name:'光污染的成因', diff:'mid', expKey:'reflect',
    question:'现代化城市的玻璃幕墙在阳光下十分刺眼，造成"光污染"，这是光发生了：',
    options:[
      { id:'A', text:'镜面反射', correct:true, explain:'✓ 玻璃幕墙表面光滑平整，反射光线朝同一方向射出，特别刺眼' },
      { id:'B', text:'漫反射', correct:false, explain:'漫反射光线射向四面八方，光线柔和，不会特别刺眼' },
      { id:'C', text:'折射', correct:false, explain:'刺眼的反射光是玻璃表面返回的，不是透过玻璃的折射光' },
      { id:'D', text:'色散', correct:false, explain:'色散与刺眼的白亮反光无关' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'光滑表面→镜面反射；粗糙表面→漫反射。'
  },
  { id:'q-virtual-side', type:'pick', name:'凸透镜成虚像的位置', diff:'mid', expKey:'lens',
    question:'物体经凸透镜成正立放大的虚像时，像与物体的位置关系是：',
    options:[
      { id:'A', text:'在透镜的同侧，且像比物离透镜更远', correct:true, explain:'✓ u＜f 成虚像时，像与物在透镜同侧，像离透镜比物更远' },
      { id:'B', text:'在透镜的两侧', correct:false, explain:'异侧成的是实像（倒立）' },
      { id:'C', text:'像与物重合', correct:false, explain:'虚像与物体不重合，且像被放大' },
      { id:'D', text:'在透镜的异侧且像比物小', correct:false, explain:'异侧缩小实像是照相机（u＞2f）的情形' }
    ],
    criteria:['answer'], criteriaWeight:{answer:100},
    promptHint:'同侧虚像（u＜f），异侧实像（u＞f）。'
  }
];

/* ===== 2. 全局状态 ===== */
const RAINBOW = ['#ef4444','#f97316','#eab308','#22c55e','#3b82f6','#6366f1','#a855f7'];
// V4.4：手绘画笔颜色语义（红=入射 蓝=反射/像 绿=折射 黑=法线/辅助）
const TOOL_COLORS = { 'free-red':'#ef4444', 'free-blue':'#3b82f6', 'free-green':'#10b981', 'free-black':'#17150e' };

const STATE = {
  problem: null,
  tool: 'free-red',
  strokes: [],         // V4.4 手绘：{tool:'free'|'rainbow', color, points:[{x,y}...]}
  undoStack: [],
  revealMode: false,
  judging: false,
  judgment: null,
  // V4.9.6：pick/multi 题型的作答（数组 = 已选项 id；空数组 = 未作答）
  pickAnswer: [],
  // V4.10.1：选择题点选即判——本题是否已作答（作答后锁定，防重复计分）
  objAnswered: false,
};

/* ===== 3. Canvas 绘图工具 ===== */
const canvas = document.getElementById('cv-judge');
const ctx = canvas ? canvas.getContext('2d') : null;

function getPos(e){
  const r = canvas.getBoundingClientRect();
  const sx = canvas.width / r.width;
  const sy = canvas.height / r.height;
  const cx = (e.touches ? e.touches[0].clientX : e.clientX) - r.left;
  const cy = (e.touches ? e.touches[0].clientY : e.clientY) - r.top;
  return { x: cx * sx, y: cy * sy };
}

// 主题变量读取（V4.2 亮/深两套主题，画布颜色跟随）
function cssVar(name, fallback){
  try {
    const v = getComputedStyle(document.body).getPropertyValue(name).trim();
    return v || fallback;
  } catch (e) { return fallback; }
}

function drawArrow(c, x1, y1, x2, y2, color, dashed){
  c.save();
  c.strokeStyle = color;
  c.fillStyle = color;
  c.lineWidth = 2.5;
  if (dashed) c.setLineDash([6, 4]);
  c.beginPath();
  c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke();
  // V4.4：箭头画在线段中点（物理绘图惯例——方向标在光线中部而非端点）
  if (!dashed) {
    const mx = (x1 + x2) / 2, my = (y1 + y2) / 2;
    const ang = Math.atan2(y2 - y1, x2 - x1);
    const ah = 10;
    c.beginPath();
    c.moveTo(mx, my);
    c.lineTo(mx - ah * Math.cos(ang - Math.PI / 6), my - ah * Math.sin(ang - Math.PI / 6));
    c.lineTo(mx - ah * Math.cos(ang + Math.PI / 6), my - ah * Math.sin(ang + Math.PI / 6));
    c.closePath();
    c.fill();
  }
  c.restore();
}

function drawMirror(c, x1, y1, x2, y2){
  c.save();
  const lineC = cssVar('--line', '#17150e');
  c.strokeStyle = lineC;
  c.lineWidth = 3;
  c.beginPath(); c.moveTo(x1, y1); c.lineTo(x2, y2); c.stroke();
  // 阴影短斜线画在反射面背后（水平镜面画下方、竖直镜面画右侧）
  c.strokeStyle = cssVar('--muted', 'rgba(23,21,14,.5)');
  c.lineWidth = 1.2;
  if (Math.abs(y2 - y1) < 2) {           // 水平镜面
    for (let x = Math.min(x1, x2) + 8; x < Math.max(x1, x2); x += 14) {
      c.beginPath();
      c.moveTo(x, y1 + 4);
      c.lineTo(x - 6, y1 + 12);
      c.stroke();
    }
  } else {                                // 竖直镜面
    const top = Math.min(y1, y2), bot = Math.max(y1, y2), mx = x1;
    for (let y = top + 8; y < bot; y += 14) {
      c.beginPath();
      c.moveTo(mx + 4, y);
      c.lineTo(mx + 12, y - 6);
      c.stroke();
    }
  }
  c.restore();
}

function drawScene(problem){
  if (!ctx) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (!problem) return;
  // V4.9.6：客观题（pick/multi）没有 scene，整个场景绘制跳过——画布只显示提示文字
  const isObj = (problem.type === 'pick' || problem.type === 'multi');
  if(isObj){
    ctx.save();
    ctx.fillStyle = cssVar('--muted', 'rgba(23,21,14,.5)');
    ctx.font = 'bold 18px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('📝 本题为客观题，请在右侧选答案', canvas.width/2, canvas.height/2);
    ctx.font = '14px sans-serif';
    ctx.fillText('（画布对客观题不生效）', canvas.width/2, canvas.height/2 + 28);
    ctx.restore();
    return;
  }

  // 底色网格（跟随 V4.2 --cvbg 主题变量：亮=纸黄，深=近黑）
  ctx.save();
  ctx.fillStyle = cssVar('--cvbg', '#fbf8ea');
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = 'rgba(128, 128, 128, .14)';
  ctx.lineWidth = 1;
  for (let x = 0; x < canvas.width; x += 40) {
    ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvas.height); ctx.stroke();
  }
  for (let y = 0; y < canvas.height; y += 40) {
    ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(canvas.width, y); ctx.stroke();
  }
  ctx.restore();

  const s = problem.scene;

  // 主光轴（凸透镜等：横向点划线）
  if (s.axis) {
    ctx.save();
    ctx.strokeStyle = cssVar('--muted', 'rgba(128,128,128,.5)');
    ctx.lineWidth = 1.4;
    ctx.setLineDash([14, 5, 3, 5]);
    ctx.beginPath();
    ctx.moveTo(0, s.axis.y);
    ctx.lineTo(canvas.width, s.axis.y);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = cssVar('--muted2', '#3d3a2c');
    ctx.font = 'bold 11px sans-serif';
    ctx.fillText('主光轴', canvas.width - 62, s.axis.y - 8);
    ctx.restore();
  }
  // 镜面（支持水平与竖直）
  if (s.mirror) {
    drawMirror(ctx, s.mirror.x1, s.mirror.y1, s.mirror.x2, s.mirror.y2);
  }
  // 透镜（凸）：淡蓝玻璃 + 主题边（V4.2 语言）
  // V4.4 修复：s.lens 是对象 {x:460}，V4.3 误当数字用导致 NaN 全部静默不渲染
  if (s.lens) {
    const Lx = s.lens.x, ax = s.axis ? s.axis.y : 300;
    ctx.save();
    ctx.fillStyle = 'rgba(24, 95, 165, 0.10)';
    ctx.strokeStyle = cssVar('--line', '#17150e');
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.ellipse(Lx, ax, 8, 190, 0, 0, Math.PI * 2);
    ctx.fill(); ctx.stroke();
    // 焦点标记（画在主光轴上）
    ctx.fillStyle = cssVar('--txt', '#17150e');
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    [['F', -s.f], ["F'", s.f], ['2F', -2 * s.f], ["2F'", 2 * s.f], ['O', 0]].forEach(([t, dx]) => {
      ctx.beginPath(); ctx.arc(Lx + dx, ax, 3, 0, Math.PI * 2); ctx.fill();
      ctx.fillText(t, Lx + dx, ax + 18);
    });
    ctx.restore();
  }
  // V4.9.6：小孔成像场景（line-hole）
  if (s.hole) {
    ctx.save();
    const holeY = s.hole.y, holeSize = s.hole.size || 4;
    // 屏障（不透光挡板）：V4.9.8 修复——原用 fillRect + 背景色绘制，在浅色底上完全看不见；
    // 改为用描边色画上下两段实线，中间天然留出小孔
    const barTop = 40, barBot = canvas.height - 40;
    ctx.strokeStyle = cssVar('--line', '#17150e');
    ctx.lineWidth = 5;
    ctx.lineCap = 'butt';
    ctx.beginPath();
    ctx.moveTo(s.hole.x, barTop);                 // 上段
    ctx.lineTo(s.hole.x, holeY - holeSize / 2);
    ctx.moveTo(s.hole.x, holeY + holeSize / 2);   // 下段
    ctx.lineTo(s.hole.x, barBot);
    ctx.stroke();
    // 小孔位置标一个小圆点，提示"光从这里穿过"
    ctx.fillStyle = '#e8862e';
    ctx.beginPath();
    ctx.arc(s.hole.x, holeY, 2.5, 0, Math.PI * 2);
    ctx.fill();
    // 屏
    if (s.screen) {
      ctx.strokeStyle = cssVar('--line', '#17150e');
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.moveTo(s.screen.x, s.screen.y1);
      ctx.lineTo(s.screen.x, s.screen.y2);
      ctx.stroke();
      // V4.9.8：屏的标注移到屏右侧偏下，避开上方的"像"文字
      ctx.fillStyle = cssVar('--txt', '#17150e');
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'left';
      ctx.fillText('光屏', s.screen.x + 10, s.screen.y2 + 20);
    }
    // V4.9.8：小孔标注移到屏障左下侧，避免压在交叉光路上
    ctx.fillStyle = cssVar('--txt', '#17150e');
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'right';
    ctx.fillText('小孔（不透光屏障）', s.hole.x - 10, barBot + 14);
    ctx.restore();
  }
  // 分界面（水/空气）
  if (s.interface) {
    ctx.save();
    ctx.strokeStyle = '#17150e';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(0, s.interface.y);
    ctx.lineTo(canvas.width, s.interface.y);
    ctx.stroke();
    // 水域淡蓝填充
    ctx.fillStyle = 'rgba(14, 165, 233, 0.08)';
    ctx.fillRect(0, s.interface.y, canvas.width, canvas.height - s.interface.y);
    ctx.fillStyle = '#185fa5';
    ctx.font = 'bold 12px sans-serif';
    ctx.fillText('空气 (n=1.0)', 30, s.interface.y - 8);
    ctx.fillText('水 (n=1.33)', 30, s.interface.y + 18);
    ctx.restore();
  }
  // 三棱镜
  if (s.prism) {
    ctx.save();
    ctx.fillStyle = 'rgba(24, 95, 165, 0.10)';
    ctx.strokeStyle = '#17150e';
    ctx.lineWidth = 2;
    const p = s.prism;
    ctx.beginPath();
    ctx.moveTo(p.cx - p.w / 2, p.cy + p.h / 2);
    ctx.lineTo(p.cx + p.w / 2, p.cy + p.h / 2);
    ctx.lineTo(p.cx, p.cy - p.h / 2);
    ctx.closePath();
    ctx.fill(); ctx.stroke();
    // V4.9.11：棱镜三顶点字母（与「光的色散」标准答案的推导对齐，方便学生对照）
    ctx.fillStyle = cssVar('--txt', '#17150e');
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText('A', p.cx, p.cy - p.h / 2 - 14);
    ctx.fillText('B', p.cx - p.w / 2 - 14, p.cy + p.h / 2 + 12);
    ctx.fillText('C', p.cx + p.w / 2 + 14, p.cy + p.h / 2 + 12);
    ctx.restore();
  }
  // V4.9.11 新增：白光入射光线（色散题的 scene.whiteIn 此前**没有任何渲染分支**，
  //   导致学生进到「光的色散」题只看见一个空棱镜，不知道该从哪里画起）
  if (s.whiteIn) {
    ctx.save();
    drawArrow(ctx, s.whiteIn.from.x, s.whiteIn.from.y, s.whiteIn.to.x, s.whiteIn.to.y, '#e8862e', false);
    ctx.fillStyle = cssVar('--txt', '#17150e');
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    ctx.fillText('白光', s.whiteIn.from.x, s.whiteIn.from.y - 16);
    ctx.restore();
  }

  // 题目元素：光源 / 物体 / 入射
  ctx.save();
  ctx.fillStyle = cssVar('--red', '#c8331f');
  ctx.font = 'bold 16px sans-serif';
  ctx.textAlign = 'center';
  if (s.source) {
    ctx.beginPath(); ctx.arc(s.source.x, s.source.y, 8, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = cssVar('--txt', '#17150e');
    ctx.fillText(s.source.label || 'S', s.source.x - 14, s.source.y - 12);
  }
  if (s.object) {
    // V4.9.10：物体统一改画成「带箭头的竖线段」（物理绘图惯例：物体用箭头表示，箭头指向
    //   表示物体正立方向——箭头一律朝上）。此前只画一条裸竖线、却在别处标 ↑，自相矛盾。
    //   约定：object.y1 = 物体上端（箭头尖），object.y2 = 物体下端（箭头尾）。
    const oTopY = Math.min(s.object.y1, s.object.y2);
    const oBotY = Math.max(s.object.y1, s.object.y2);
    ctx.strokeStyle = cssVar('--red', '#c8331f');
    ctx.fillStyle = cssVar('--red', '#c8331f');
    ctx.lineWidth = 3;
    ctx.beginPath();
    ctx.moveTo(s.object.x, oBotY);
    ctx.lineTo(s.object.x, oTopY);
    ctx.stroke();
    // 箭头尖（朝上）——画在物体顶端，让学生看出"这是个正立的物体"
    ctx.beginPath();
    ctx.moveTo(s.object.x, oTopY);
    ctx.lineTo(s.object.x - 6, oTopY + 12);
    ctx.lineTo(s.object.x + 6, oTopY + 12);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = cssVar('--txt', '#17150e');
    // V4.9.10：字母标注改由各题自己决定（见 drawEndpointLabels），此处不再硬写 label。
    //   （平面镜题原本在这里多画了一个 "AB" 在物体中部，与端点上的 A / B 重复，已去掉）
    if (s.object.label && s.object.label !== 'AB') {
      ctx.fillText(s.object.label, s.object.x + 12, (oTopY + oBotY) / 2);
    }
  }
  if (s.incident) {
    drawArrow(ctx, s.incident.from.x, s.incident.from.y, s.incident.to.x, s.incident.to.y, '#e8862e', false);
  }
  ctx.restore();

  // 标准答案（仅在 revealMode 显示）
  if (STATE.revealMode && problem.std) {
    drawStandardAnswer(problem);
  }

  // 画学生笔迹
  STATE.strokes.forEach(s => drawStroke(s));

  // 高亮判卷结果：marks（V4.4 模型相对坐标判卷点）+ highlights（遗留几何模式）
  const J = STATE.judgment;
  if (J && J.highlights) J.highlights.forEach(h => drawHighlight(h));
  if (J && J.marks && J.marks.length) {
    J.marks.forEach(m => {
      if (typeof m.x !== 'number' || typeof m.y !== 'number') return;
      drawHighlight({ type: 'point', x: m.x * canvas.width, y: m.y * canvas.height, ok: !!m.ok });
      if (m.label) {
        ctx.save();
        ctx.fillStyle = m.ok ? cssVar('--blue', '#185fa5') : cssVar('--red', '#c8331f');
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'center';
        ctx.fillText(m.label, m.x * canvas.width, m.y * canvas.height + 24);
        ctx.restore();
      }
    });
  }
}

function drawStroke(s){
  if (!ctx) return;
  // V4.4：自由手绘笔画（平滑曲线 + 弧长中点方向箭头）
  if (s.tool === 'free' || s.tool === 'rainbow') {
    const pts = s.points;
    if (!pts || pts.length < 2) return;
    ctx.save();
    ctx.strokeStyle = s.color;
    ctx.fillStyle = s.color;
    ctx.lineWidth = 2.5;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length - 1; i++) {
      const mx = (pts[i].x + pts[i + 1].x) / 2, my = (pts[i].y + pts[i + 1].y) / 2;
      ctx.quadraticCurveTo(pts[i].x, pts[i].y, mx, my);
    }
    const lastP = pts[pts.length - 1];
    ctx.lineTo(lastP.x, lastP.y);
    ctx.stroke();
    // 弧长中点画方向箭头（黑笔=法线不画箭头；红/蓝/绿/彩虹为光线，画箭头）
    if (s.tool === 'rainbow' || s.color !== TOOL_COLORS['free-black']) {
      let total = 0; const segs = [];
      for (let i = 1; i < pts.length; i++) {
        const d = Math.hypot(pts[i].x - pts[i - 1].x, pts[i].y - pts[i - 1].y);
        segs.push(d); total += d;
      }
      if (total > 24) {
        let acc = 0; const half = total / 2; let idx = 0;
        for (; idx < segs.length; idx++) { acc += segs[idx]; if (acc >= half) break; }
        const a = pts[idx], b = pts[Math.min(idx + 1, pts.length - 1)];
        const ang = Math.atan2(b.y - a.y, b.x - a.x), ah = 10;
        const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
        ctx.beginPath();
        ctx.moveTo(mx, my);
        ctx.lineTo(mx - ah * Math.cos(ang - Math.PI / 6), my - ah * Math.sin(ang - Math.PI / 6));
        ctx.lineTo(mx - ah * Math.cos(ang + Math.PI / 6), my - ah * Math.sin(ang + Math.PI / 6));
        ctx.closePath();
        ctx.fill();
      }
    }
    ctx.restore();
    return;
  }
  // 旧语义工具（V4.3 遗留兼容，手绘模式下不再产生）
  if (s.tool === 'incident') drawArrow(ctx, s.from.x, s.from.y, s.to.x, s.to.y, cssVar('--red', '#ef4444'), false);
  else if (s.tool === 'reflect') drawArrow(ctx, s.from.x, s.from.y, s.to.x, s.to.y, cssVar('--blue', '#3b82f6'), false);
  else if (s.tool === 'refract') drawArrow(ctx, s.from.x, s.from.y, s.to.x, s.to.y, '#10b981', false);
  else if (s.tool === 'normal') drawArrow(ctx, s.from.x, s.from.y, s.to.x, s.to.y, cssVar('--txt', '#000000'), true);
  else if (s.tool === 'mirror') drawMirror(ctx, s.from.x, s.from.y, s.to.x, s.to.y);
  else if (s.tool === 'angle') {
    // 扇形弧
    ctx.save();
    ctx.strokeStyle = '#a855f7';
    ctx.fillStyle = '#a855f7';
    ctx.lineWidth = 1.5;
    const r = 30;
    ctx.beginPath();
    ctx.arc(s.at.x, s.at.y, r, s.startA, s.endA);
    ctx.stroke();
    if (s.label) {
      ctx.font = 'bold 13px sans-serif';
      ctx.textAlign = 'center';
      const mid = (s.startA + s.endA) / 2;
      ctx.fillText(s.label, s.at.x + (r + 12) * Math.cos(mid), s.at.y + (r + 12) * Math.sin(mid));
    }
    ctx.restore();
  }
  else if (s.tool === 'label' && s.text) {
    ctx.save();
    ctx.fillStyle = cssVar('--txt', '#17150e');
    ctx.font = '14px sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText(s.text, s.at.x, s.at.y);
    ctx.restore();
  }
}

function drawHighlight(h){
  if (!ctx) return;
  ctx.save();
  if (h.type === 'point') {
    ctx.fillStyle = h.ok ? cssVar('--blue', '#185fa5') : cssVar('--red', '#c8331f');
    ctx.beginPath();
    ctx.arc(h.x, h.y, 8, 0, Math.PI * 2);
    ctx.fill();
    ctx.strokeStyle = cssVar('--cvbg', '#fbf8ea');
    ctx.lineWidth = 2;
    ctx.stroke();
  } else if (h.type === 'line') {
    ctx.strokeStyle = h.ok ? cssVar('--blue', '#185fa5') : cssVar('--red', '#c8331f');
    ctx.lineWidth = 4;
    ctx.globalAlpha = 0.4;
    ctx.beginPath();
    ctx.moveTo(h.from.x, h.from.y);
    ctx.lineTo(h.to.x, h.to.y);
    ctx.stroke();
  }
  ctx.restore();
}

/* V4.9.10 新增：带箭头的竖直线段（物体 / 像 的统一画法）
   x        —— 线段所在的横坐标
   yBot     —— 尾端（下端）
   yTop     —— 箭头尖（上端）
   color    —— 颜色
   dashed   —— 是否虚线（虚像必须虚线：这是判分点之一，别漏）
   说明：物理绘图里"物体"和"像"都用箭头表示，箭头指向 = 正立方向。
        正立的物/像箭头朝上；倒立的像由调用方把 yTop/yBot 反过来传即可（箭头自然朝下）。
        箭头三角形不用线型，始终实心填充（虚线只作用于杆身）。 */
function drawObjectArrow(x, yBot, yTop, color, dashed){
  if (!ctx) return;
  ctx.save();
  ctx.strokeStyle = color;
  ctx.fillStyle = color;
  ctx.lineWidth = 3;
  ctx.lineCap = 'butt';
  if (dashed) ctx.setLineDash([6, 5]);
  ctx.beginPath();
  ctx.moveTo(x, yBot);
  ctx.lineTo(x, yTop);
  ctx.stroke();
  ctx.setLineDash([]);                   // 箭头实心，不受虚线影响
  const ah = 12, aw = 6;
  const dir = (yTop <= yBot) ? 1 : -1;   // 箭头尖朝上时 dir=1（三角形画在 yTop 下方）
  ctx.beginPath();
  ctx.moveTo(x, yTop);
  ctx.lineTo(x - aw, yTop + dir * ah);
  ctx.lineTo(x + aw, yTop + dir * ah);
  ctx.closePath();
  ctx.fill();
  ctx.restore();
}

/* V4.9.10 新增：把两个字母分别标在线段的上下两端
   —— 端点字母（A/B 或 A'/B'）必须各归各位，不能挤在一行，
      否则学生看不出哪个字母对应哪一端、"像与物关于镜面对称"就没有着落点。 */
function drawEndpointLabels(x, y1, y2, topLabel, botLabel, color){
  if (!ctx) return;
  const topY = Math.min(y1, y2), botY = Math.max(y1, y2);
  ctx.save();
  ctx.fillStyle = color;
  ctx.font = 'bold 13px sans-serif';
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(topLabel, x - 14, topY);          // 上端字母：放线段左侧，避开箭头尖
  ctx.fillText(botLabel, x - 14, botY);          // 下端字母：同侧，保持整齐
  ctx.restore();
}

/* V4.9.11 新增：直角符号（垂直标记）——"某线段垂直于某条线"的规范画法。
   物理作图里只要出现垂足（如平面镜成像题中"物像对应点的连线垂直于镜面"），
   就必须在垂足处标出直角符号；否则学生无法判断这条连线到底是"垂直"还是"随手一画"。
   mx,my   —— 垂足（两线交点）
   openDir —— 小方块在水平线的哪一侧：+1 = 画在水平线下方，-1 = 画在水平线上方
   size    —— 方块边长（px）
   说明：符号只画"两条腿"——一条沿水平线往左、一条沿竖直线往 openDir 侧，
        两条腿 + 隐含的两条已知直线自然围出一个直角小方块。 */
function drawRightAngleMark(mx, my, openDir, size, color){
  if (!ctx) return;
  const s = size || 13, dir = (openDir >= 0) ? 1 : -1;
  ctx.save();
  ctx.strokeStyle = color || cssVar('--line', '#17150e');
  ctx.lineWidth = 1.6;
  ctx.setLineDash([]);                 // 直角符号自身永远是实线
  ctx.beginPath();
  ctx.moveTo(mx - s, my);              // 腿①：沿水平线（往镜面外侧）
  ctx.lineTo(mx - s, my + dir * s);    // 拐角
  ctx.lineTo(mx, my + dir * s);        // 腿②：沿竖直线
  ctx.stroke();
  ctx.restore();
}

/* V4.9.11 新增：通用虚线（法线 / 反向延长线）——统一样式，避免各题各写一套 */
function drawDashedLine(x1, y1, x2, y2, color, dash){
  if (!ctx) return;
  ctx.save();
  ctx.strokeStyle = color || cssVar('--line', '#17150e');
  ctx.lineWidth = 1.6;
  ctx.setLineDash(dash || [6, 5]);
  ctx.beginPath();
  ctx.moveTo(x1, y1);
  ctx.lineTo(x2, y2);
  ctx.stroke();
  ctx.setLineDash([]);
  ctx.restore();
}

/* V4.9.11 新增：角的圆弧 + 字母标注（入射角 i / 折射角 r / 反射角 r 共用）
   at      —— 角的顶点
   a1,a2   —— 两条边的方向角（弧度）
   cw      —— 是否顺时针扫（ctx.arc 的 anticlockwise 取反）
   radius  —— 弧半径
   label   —— 标在弧中点外侧的字母（可为空）
   labelDX/DY —— 字母的额外微调（避开光线） */
function drawAngleArc(at, a1, a2, cw, radius, label, color){
  if (!ctx) return;
  const r = radius || 40;
  ctx.save();
  ctx.strokeStyle = color || cssVar('--muted2', '#3d3a2c');
  ctx.lineWidth = 1.4;
  ctx.setLineDash([]);
  ctx.beginPath();
  ctx.arc(at.x, at.y, r, a1, a2, !!cw);
  ctx.stroke();
  if (label){
    // 弧中点方向再往外挪 16px 放字母，保证不压在弧线上
    let mid = (a1 + a2) / 2;
    if (Math.abs(a2 - a1) > Math.PI) mid += Math.PI;   // 扫过 180° 时取补角方向
    ctx.fillStyle = color || cssVar('--txt', '#17150e');
    ctx.font = 'bold 13px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, at.x + (r + 16) * Math.cos(mid), at.y + (r + 16) * Math.sin(mid));
  }
  ctx.restore();
}

function drawStandardAnswer(p){
  if (!ctx) return;
  ctx.save();
  ctx.globalAlpha = 0.55;
  const blueC = cssVar('--blue', '#185fa5');
  const lineC = cssVar('--line', '#17150e');
  if (p.id === 'reflect') {
    const o = p.std.incidentPoint, d = p.std.normalDir;
    // 法线（双向虚线）
    if (d && o) {
      ctx.strokeStyle = lineC;
      ctx.lineWidth = 1.6;
      ctx.setLineDash([4, 6]);
      ctx.beginPath();
      ctx.moveTo(o.x - 130 * d.x, o.y - 130 * d.y);
      ctx.lineTo(o.x + 130 * d.x, o.y + 130 * d.y);
      ctx.stroke();
      ctx.setLineDash([]);
    }
    // V4.4：补画标准入射光线 S→O（红）与标准反射光线 O→(0.707,-0.707)×160（蓝）
    const src = p.scene.source;
    if (src && o) {
      ctx.lineWidth = 2.2;
      drawArrow(ctx, src.x, src.y, o.x, o.y, cssVar('--red', '#c8331f'), false);
      const dx = (o.x - src.x), dy = (o.y - src.y), L = Math.hypot(dx, dy);
      // 反射向量 = 入射单位向量关于法线镜像：r = d - 2(d·n)n
      const ux = dx / L, uy = dy / L;
      const dot = ux * d.x + uy * d.y;
      const rx = ux - 2 * dot * d.x, ry = uy - 2 * dot * d.y;
      drawArrow(ctx, o.x, o.y, o.x + 160 * rx, o.y + 160 * ry, blueC, false);
      // 角度弧提示（i 与 r）
      ctx.strokeStyle = cssVar('--muted2', '#3d3a2c');
      ctx.lineWidth = 1.4;
      const r0 = Math.atan2(src.y - o.y, src.x - o.x);   // 入射方向（从 O 指向 S 的反向即来向）
      ctx.beginPath();
      ctx.arc(o.x, o.y, 34, -Math.PI / 2, r0 < -Math.PI / 2 ? r0 + Math.PI * 2 : r0, false);
      ctx.stroke();
      ctx.beginPath();
      const r1 = Math.atan2(ry, rx);
      ctx.arc(o.x, o.y, 34, r1, -Math.PI / 2, false);
      ctx.stroke();
      ctx.fillStyle = cssVar('--txt', '#17150e');
      ctx.font = 'bold 13px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('i', o.x - 46, o.y - 22);
      ctx.fillText('r', o.x + 46, o.y - 22);
    }
  } else if (p.id === 'mirror') {
    // 对称辅助线：物与像的对应点虚线连线（垂直于竖直镜面）
    const obj = p.scene.object, img = p.std.imagePos;
    if (obj && img) {
      // V4.9.10：物也补上朝上的箭头（与全站"物体=带箭头竖线"的画法统一）
      drawObjectArrow(obj.x, obj.y2, obj.y1, cssVar('--red', '#c8331f'));
      // V4.9.10：像 A'B' 画成带箭头的竖线——正立虚像 ⇒ 箭头同样朝上
      drawObjectArrow(img.x, img.y2, img.y1, blueC);
      ctx.strokeStyle = blueC;
      ctx.lineWidth = 1.6;
      ctx.setLineDash([4, 6]);
      ctx.beginPath();
      ctx.moveTo(obj.x, obj.y1); ctx.lineTo(img.x, img.y1);
      ctx.moveTo(obj.x, obj.y2); ctx.lineTo(img.x, img.y2);
      ctx.stroke();
      ctx.setLineDash([]);
      // V4.9.11：两条对称辅助线垂直于镜面 ⇒ 在两处垂足各补一个直角符号。
      //   原来只有一条虚线横穿镜面、没有任何垂直标记，学生看不出这条线是"特意画的垂线"
      //   还是"随手连的线"，"物像连线垂直于镜面、故物距=像距"这个推理也就没有落点。
      //   小方块分别朝画面中部的空处开口（上一条朝下、下一条朝上），避免压住 A/B 字母。
      const mxMark = p.scene.mirror.x1;
      // 镜面可能在物体左侧或右侧，方块要画在物体这一侧才不会跑到像那边
      const openToObj = (obj.x < mxMark) ? -1 : +1;   // -1 = 方块沿水平线往左伸
      drawRightAngleMark(mxMark, obj.y1, +openToObj, 13, blueC);
      drawRightAngleMark(mxMark, obj.y2, -openToObj, 13, blueC);
      // V4.9.10：字母分别落在"自己那根线段"的两端——
      //   物：A 在上端、B 在下端；像：A' 在上端、B' 在下端。
      //   （旧版把 A、B 挤在物中部一行、A'/B' 浮在像末端外侧，看不出谁是上端谁是下端）
      drawEndpointLabels(obj.x, obj.y1, obj.y2, 'A', 'B', cssVar('--txt', '#17150e'));
      drawEndpointLabels(img.x, img.y1, img.y2, "A'", "B'", blueC);
      // V4.9.11：把"物距 = 像距"这层关系直接标在图上，替学生把结论落到数字
      ctx.fillStyle = blueC;
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('物距 ' + p.std.objectDistance + 'px = 像距 ' + p.std.imageDistance + 'px',
        (obj.x + img.x) / 2, Math.min(obj.y1, obj.y2) - 22);
    }
  } else if (p.id === 'lens') {
    // V4.4：补画三条特殊成像光线（汇聚于像顶点），倒立实像箭头
    const obj = p.scene.object, Lx = p.scene.lens.x, f = p.scene.f, ax = p.scene.axis.y;
    const img = p.std.imagePos;
    if (obj && img) {
      const top = { x: obj.x, y: Math.min(obj.y1, obj.y2) };      // 物顶点 (200,200)
      const imgTop = { x: img.x, y: Math.max(img.y1, img.y2) };   // 像顶点 (576,344)（倒立在轴下方）
      ctx.lineWidth = 2;
      // 光线①：物顶平行主光轴 → 透镜 → 折向 F' → 像顶点
      drawArrow(ctx, top.x, top.y, Lx, top.y, '#e8862e', false);
      drawArrow(ctx, Lx, top.y, imgTop.x, imgTop.y, '#e8862e', false);
      // 光线②：物顶过光心直线 → 像顶点
      drawArrow(ctx, top.x, top.y, imgTop.x, imgTop.y, '#e8862e', false);
      // 光线③：物顶过 F（物方焦点）→ 透镜 → 平行主光轴 → 像顶点
      const fl = Lx - f;                                          // 物方焦点 x=380
      const lensY3 = top.y + (ax - top.y) * (Lx - top.x) / (fl - top.x);
      drawArrow(ctx, top.x, top.y, Lx, lensY3, '#e8862e', false);
      drawArrow(ctx, Lx, lensY3, imgTop.x, lensY3, '#e8862e', false);
      // 像（倒立实像）：V4.9.10 修正箭头朝向——倒立像的箭头应朝下（指向主光轴下方），
      //   即"箭头尖 = 像的下端"。旧版写 drawArrow(ax → img.y2) 画出的是朝下箭头，
      //   但那时 img.y1..y2 只是"像占的竖直范围"，箭头朝下却说成倒立，容易与"增长方向"混淆。
      //   现统一用 drawObjectArrow(尾端=上端, 尖=下端) 明确表达"倒立"。
      drawObjectArrow(img.x, img.y1, img.y2, blueC);
      ctx.setLineDash([]);
      ctx.fillStyle = blueC;
      ctx.font = 'bold 13px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'alphabetic';
      ctx.fillText('像（倒立缩小实像）', img.x + 8, img.y2 + 22);
    }
  } else if (p.id === 'line-hole') {
    // V4.9.8：小孔成像标准答案——光沿直线传播，物顶/物底的光各走一条笔直的线穿过小孔到屏
    //   修复：旧版把「物→孔」「孔→屏」拆成 4 段 drawArrow，每段中点各画一个箭头，
    //         在孔的位置两个箭头尖对尖，视觉上像光线在小孔处"拐弯"（科学性错误观感）。
    //   现改为：每条光线用一条完整直线（物→屏）绘制，孔处不打断、不放箭头，
    //         箭头只画整条光线的中点，明确表达"光沿直线传播"。
    const obj = p.scene.object, img = p.std.imagePos, hole = p.scene.hole;
    if(obj && img && hole){
      ctx.lineWidth = 2;
      const objTop = { x: obj.x, y: obj.y1 }, objBot = { x: obj.x, y: obj.y2 };
      // 光路①：物顶（上）—— 直线穿过小孔 —— 像的下端（y2）
      //   倒立成像：物顶的光落到像的下端，所以是 img.y2
      drawArrow(ctx, objTop.x, objTop.y, img.x, img.y2, '#e8862e', false);
      // 光路②：物底（下）—— 直线穿过小孔 —— 像的上端（y1）
      drawArrow(ctx, objBot.x, objBot.y, img.x, img.y1, '#e8862e', false);
      // 标出两条光线的交点即小孔（用一个小圆点强调"光在此处依然走直线"）
      ctx.save();
      ctx.fillStyle = '#e8862e';
      ctx.beginPath();
      ctx.arc(hole.x, hole.y, 3.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
      // 像（倒立实像）：V4.9.10 修正——箭头朝下表示倒立（尖=像的下端）
      drawObjectArrow(img.x, img.y1, img.y2, blueC);
      ctx.fillStyle = blueC;
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'left';
      // V4.9.8：标注移到像的右上侧空白处，不再压在屏线或光路上
      ctx.fillText('像（倒立等大实像）', img.x + 16, img.y2 + 22);
    }
  } else if (p.id === 'lens-virtual') {
    /* V4.9.11 重写：u<f 凸透镜成正立放大虚像 —— 三条特殊光线的规范画法
       -------- 本题几何（scene: lens.x=460, f=80, axis.y=300；obj.x=400, y 300→240）--------
       物：x=400，高 60（底在主轴 y=300、顶 y=240）。u = 460-400 = 60 < f = 80 ✓
       焦点：F(380,300)  F'(540,300)
       虚像：v = -240（同侧）⇒ x = 460-240 = 220；放大率 m = f/(f-u) = 4 ⇒ 像高 240
             像底 (220,300)、像顶 (220,60)，正立。
       -------- 三条特殊光线的真实光路（V4.9.11 之前这里是错的）--------
       ① 物顶(400,240) 平行主光轴 → 透镜(460,240) → 折射后过 F'(540,300) 向右下射出（实线）。
          真实出射光线的反向延长线（虚线）交左上方于像顶 (220,60) —— 虚像就是这条反向延长线的交点。
          校验：过 (460,240)、(540,300) 的直线斜率 0.75，向左延伸到 x=220 时 y=240-0.75*240=60 ✓
       ② 物顶(400,240) 过光心 O(460,300) → 方向不变继续向右下射出（实线）。
          出射光线的反向延长线（虚线）同样过像顶 (220,60)。
          校验：斜率 1，向左延伸到 x=220 时 y=240-180=60 ✓
       ③ 物顶(400,240) 的延长线过物方焦点 F(380,300) 的光线 → 折射后平行主光轴射出（实线 y=60）。
          该平行光的反向延长线（虚线）水平向左，交于像顶 (220,60) ✓
          校验：F(380,300)、物顶(400,240)、入射线与透镜交点(460,60) 三点共线（斜率 -3）✓
       -------- 旧版错在哪 --------
       · 光线①：把"透镜→折向F'"画成了"透镜→像顶"的虚线，方向反了——真实光线是往右下的，
         虚线才是往左的反向延长线，两者被合并成一条，学生看不出哪段是真光、哪段是延长线；
       · 光线②：整条虚线从物顶直接连到像顶，**没有画"物顶→光心"这段真实光线**，
         也没画光心之后的出射段，等于把光心当成"透不过去"的黑箱；
       · 光线③：压根没画（过焦点 F 的光线折射后平行主光轴是本题第三个必画要素）。
       -------- 本次改法 --------
       每条光线都拆成"实线段（真实光路，带箭头）+ 虚线段（反向延长线，不带箭头）"，
       三段虚线共同交于像顶 (220,60)，把"虚像是反向延长线的交点"这件事画得明明白白。 */
    const obj = p.scene.object, img = p.std.imagePos, Lx = p.scene.lens.x, f = p.scene.f, ax = p.scene.axis.y;
    if (obj && img) {
      const rayC = '#e8862e';
      const top    = { x: obj.x, y: Math.min(obj.y1, obj.y2) };   // 物顶 (400,240)
      const imgTop = { x: img.x, y: Math.min(img.y1, img.y2) };   // 像顶 (220, 60)
      const imgBot = { x: img.x, y: Math.max(img.y1, img.y2) };   // 像底 (220,300)
      const FL = Lx - f;                                          // F  x=380
      const FR = Lx + f;                                          // F' x=540
      ctx.lineWidth = 2;

      // —— 光线① 平行主光轴 → 过 F' ——
      drawArrow(ctx, top.x, top.y, Lx, top.y, rayC, false);              // 物顶 → 透镜（实线）
      // 出射方向：从 (Lx,top.y) 指向 F'(FR,ax)，延长一小段画箭头
      (function () {
        const dx = FR - Lx, dy = ax - top.y, L = Math.hypot(dx, dy);
        const ux = dx / L, uy = dy / L, len = 135;
        drawArrow(ctx, Lx, top.y, Lx + ux * len, top.y + uy * len, rayC, false);   // 真实出射光（实线）
      })();
      drawArrow(ctx, Lx, top.y, imgTop.x, imgTop.y, rayC, true);          // 反向延长线（虚线）→ 像顶

      // —— 光线② 过光心 O → 方向不变 ——
      const ox = Lx, oy = ax;
      drawArrow(ctx, top.x, top.y, ox, oy, rayC, false);                  // 物顶 → 光心（实线）
      (function () {
        const dx = ox - top.x, dy = oy - top.y, L = Math.hypot(dx, dy);
        const ux = dx / L, uy = dy / L, len = 105;
        drawArrow(ctx, ox, oy, ox + ux * len, oy + uy * len, rayC, false); // 过光心后继续（实线）
      })();
      // 反向延长线只画"物顶以外"的那一段——物顶到光心这段已经是实线，再叠虚线会糊成一片
      drawArrow(ctx, top.x, top.y, imgTop.x, imgTop.y, rayC, true);

      // —— 光线③ 过物方焦点 F → 折射后平行主光轴 ——
      // 物顶(400,240) 的延长线过 F(380,300)：直线斜率 -3，与透镜面 x=460 交于 y=60
      const yAtLens = top.y + (ax - top.y) * (Lx - top.x) / (FL - top.x);
      drawArrow(ctx, top.x, top.y, Lx, yAtLens, rayC, false);             // 物顶 → 透镜（实线）
      drawArrow(ctx, Lx, yAtLens, Lx + 80, yAtLens, rayC, false);         // 折射后平行主光轴（实线）
      drawArrow(ctx, Lx, yAtLens, imgTop.x, imgTop.y, rayC, true);        // 反向延长线（虚线）→ 像顶

      // —— 关键点：光心 O 与两个焦点都点一下，帮助学生把三条线对上号 ——
      ctx.save();
      ctx.fillStyle = cssVar('--txt', '#17150e');
      [[ox, oy], [FL, ax], [FR, ax]].forEach(function (ptk) {
        ctx.beginPath(); ctx.arc(ptk[0], ptk[1], 3.2, 0, Math.PI * 2); ctx.fill();
      });
      ctx.restore();

      // 虚像（正立放大 ⇒ 箭头朝上；虚像必须虚线——这是判分点之一）
      drawObjectArrow(img.x, imgBot.y, imgTop.y, blueC, true);
      ctx.fillStyle = blueC;
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText('虚像（正立放大、与物同侧、虚线）', img.x + 90, imgTop.y - 34);
      ctx.font = 'bold 11px sans-serif';
      ctx.fillText('三条虚线反向延长后交于像顶', img.x + 90, imgTop.y - 18);
      // V4.9.11：三条光线的名字必须**贴着自己那条线**标注，否则学生看到一堆橙线分不清谁是谁。
      //   ① 的实线在主轴上方 y=240 处往右走 → 标在它上方
      //   ② 的实线过光心后往右下走        → 标在它右下方的空白处
      //   ③ 的实线是 y=60 的水平线        → 标在它右上方
      //   注意画布只有 920 宽，文字一律**右对齐**贴着右边缘内缩 12px，
      //   否则 ①/③ 这类长标签会像之前那样被裁掉一半（实测溢出 200+ px）。
      ctx.font = 'bold 11px sans-serif';
      ctx.fillStyle = rayC;
      ctx.textAlign = 'right';
      ctx.fillText('① 平行主光轴 → 折射后过 F′', canvas.width - 12, top.y - 14);
      ctx.fillText('③ 过 F 的光线 → 折射后平行主光轴', canvas.width - 12, yAtLens - 13);
      ctx.fillText('② 过光心的光线 → 方向不变', Lx + 300, oy + 66);
    }
  } else if (p.id === 'refract') {
    /* V4.9.11 新增：光的折射（空气→水）标准答案
       —— V4.9.6~V4.9.10 期间这道题**根本没有标准答案分支**，学生点「👁 查看标准答案」
          什么都不会发生（drawStandardAnswer 里没有 p.id === 'refract' 这一支，直接落到函数尾部）。
          与它一同缺失的还有 'disperse'（光的色散），见下一个分支。
       -------- 本题几何（scene: interface.y=300；incident 247,171 → 400,300）--------
       入射点 O(400,300)；入射光线来自左上方。
       入射角 i = 50°（入射光线与法线的夹角，校验：Δx=153, Δy=129 ⇒ arctan(153/129)=49.8° ✓）
       折射角 r = 35.2°（sin r = sin50°/1.33），折射光线在法线**另一侧**、偏向法线，画在水中。 */
    const O = p.scene.incident.to, I = p.scene.incident.from;
    const ay = p.scene.interface.y;
    const iDeg = p.std.incidentAngle, rDeg = p.std.refractionAngle;
    const iRad = iDeg * Math.PI / 180, rRad = rDeg * Math.PI / 180;
    const redC = cssVar('--red', '#c8331f'), greenC = '#10b981';
    // ① 法线：过 O 且垂直于界面（竖直），双向虚线（空气侧 + 水侧都要画）
    drawDashedLine(O.x, ay - 150, O.x, ay + 150, lineC, [6, 5]);
    // ② 入射光线（红，实线带箭头）
    drawArrow(ctx, I.x, I.y, O.x, O.y, redC, false);
    // ③ 折射光线（绿，实线带箭头）：在法线右侧、水中，与法线夹角 r=35.2°
    const rl = 175;
    const rx = O.x + rl * Math.sin(rRad), ry = O.y + rl * Math.cos(rRad);
    drawArrow(ctx, O.x, O.y, rx, ry, greenC, false);
    // ④ 入射点标记
    ctx.save();
    ctx.fillStyle = cssVar('--txt', '#17150e');
    ctx.beginPath(); ctx.arc(O.x, O.y, 3.4, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
    // ⑤ 角的圆弧：i 在法线左侧（空气侧），r 在法线右侧（水侧）
    //    入射光线"来向"（从 O 指向 I）的方向角，与向上法线（-90°）之间夹出 i
    const aI = Math.atan2(I.y - O.y, I.x - O.x);          // ≈ -139.9°
    drawAngleArc(O, -Math.PI / 2, aI, true, 44, 'i', cssVar('--muted2', '#3d3a2c'));
    const aR = Math.atan2(ry - O.y, rx - O.x);            // ≈ +54.8°
    drawAngleArc(O, aR, Math.PI / 2, false, 44, 'r', cssVar('--muted2', '#3d3a2c'));
    // ⑥ 把角度数值直接标上（学生自查用）
    ctx.save();
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = cssVar('--txt', '#17150e');
    ctx.fillText('i = ' + iDeg + '°', O.x - 74, O.y - 52);
    ctx.fillStyle = greenC;
    ctx.fillText('r ≈ ' + rDeg.toFixed(1) + '°', O.x + 76, O.y + 62);
    // ⑦ 结论：空气中的角总是大的
    ctx.fillStyle = cssVar('--muted2', '#3d3a2c');
    ctx.font = 'bold 12px sans-serif';
    ctx.fillText('r < i：光从空气斜射入水，折射光线偏向法线', O.x, ay + 190);
    ctx.restore();
  } else if (p.id === 'disperse') {
    /* V4.9.12 重写：光的色散（三棱镜）标准答案 —— 改为**按折射定律真实追迹**
       ============================ 上一版（V4.9.11）错在哪 ============================
       V4.9.11 是"手摆"的：出射点 Pout 直接硬编码 tOut=0.48 → (488.8, 256)，
       而真实出射点是 (491.8, 266.1)，偏离 10.6px ⇒ 出射点根本没落在右腰 AC 上。
       棱镜内部那段则是 Pin→Pout 拉一条直线，方向角恰好也等于真实值 +5.66°（纯属巧合，
       因为两端点都贴在真实路径附近），但出射扇面又用 th0=12°~th1=33° 这套**与真实
       净偏折 18.09° 不吻合**的角度 ⇒ 学生看到的是"进去一个方向、出来另一套方向"，
       两次折射的偏折量对不上，所以显得"画得不对"。
       ============================ 本版做法 ============================
       完全按折射定律 n₁sin i = n₂sin r 逐面追迹（玻璃 n=1.5）：
         ① 入射白光水平射入左腰 AB
         ② 第 1 次折射 空气→玻璃：偏向法线，转向棱镜底边
         ③ 沿真实折射方向在棱镜内前进，**求与右腰 AC 的真实交点**作为出射点
         ④ 第 2 次折射 玻璃→空气：偏离法线，继续转向底边
       核算（n=1.5，入射点 y=260）：
         左腰法线指向空气侧 (-0.9578,-0.2873)，入射角 i₁ = 16.70° → 折射角 r₁ = 11.05°
         ⇒ 棱镜内方向 +5.66°；右腰法线指向玻璃侧 (-0.9578, +0.2873)，
           玻璃内入射角 i₂ = 22.35° → 出射角 r₂ = 34.62°（sin r₂ = 0.5683）
         ⇒ 出射方向 +18.09°
       净偏折 = 18.09°，**两次都向下**（都朝棱镜底边）—— 这才是教材想表达的
       "光被折向棱镜底边"，不是"画错了"。
       7 色光以 18.09° 为中心、按紫光偏折最大/红光最小展开（离散度取 ±5°，
       与实测色散角量级相符，且保证扇面不溢出画布）。 */
    const pr = p.scene.prism;
    const apex = { x: pr.cx, y: pr.cy - pr.h / 2 };            // A
    const bl   = { x: pr.cx - pr.w / 2, y: pr.cy + pr.h / 2 }; // B
    const br   = { x: pr.cx + pr.w / 2, y: pr.cy + pr.h / 2 }; // C

    // ---- 小工具（局部，不污染全局） ----
    const _n = function (v) { const l = Math.hypot(v.x, v.y) || 1; return { x: v.x / l, y: v.y / l }; };
    const _sb = function (a, b) { return { x: a.x - b.x, y: a.y - b.y }; };
    const _dt = function (a, b) { return a.x * b.x + a.y * b.y; };
    const _ml = function (a, k) { return { x: a.x * k, y: a.y * k }; };
    const _ad = function (a, b) { return { x: a.x + b.x, y: a.y + b.y }; };

    /* 折射定律：d=入射单位方向，nv=指向**入射侧**的界面法线，返回折射单位方向（全反射返回 null） */
    const refractDir = function (d, nv, n1, n2) {
      let n2v = nv, cosi = -_dt(n2v, d);
      if (cosi < 0) { n2v = _ml(n2v, -1); cosi = -_dt(n2v, d); }
      const eta = n1 / n2;
      const k = 1 - eta * eta * (1 - cosi * cosi);
      if (k < 0) return null;                       // 全反射
      const sq = Math.sqrt(k);
      return _n(_ad(_ml(d, eta), _ml(n2v, eta * cosi - sq)));
    };
    /* 射线 pin + s·dir 与直线 段(a→b) 求交，返回交点或 null */
    const hitLine = function (pin, dir, a, b) {
      const e = _sb(b, a), den = dir.x * e.y - dir.y * e.x;
      if (Math.abs(den) < 1e-9) return null;        // 平行
      const f = _sb(a, pin);
      const s = (f.x * e.y - f.y * e.x) / den;
      if (s <= 0) return null;                      // 反方向
      return { p: { x: pin.x + dir.x * s, y: pin.y + dir.y * s }, s: s };
    };

    // ---- 几何：三个面的"指向棱镜内部"的单位法线 ----
    const dAB = _n(_sb(apex, bl));  let nAB = { x: -dAB.y, y: dAB.x };
    if (_dt(nAB, _sb(br, bl)) < 0) nAB = _ml(nAB, -1);
    const dAC = _n(_sb(br, apex));  let nAC = { x: -dAC.y, y: dAC.x };
    if (_dt(nAC, _sb(bl, apex)) < 0) nAC = _ml(nAC, -1);

    // ---- 入射点：水平白光与左腰 AB 的交点 ----
    const wFrom = (p.scene.whiteIn && p.scene.whiteIn.from) || { x: 100, y: pr.cy };
    const yIn = wFrom.y;
    const Pin = hitLine(wFrom, { x: 1, y: 0 }, bl, apex);
    if (!Pin) { ctx.restore(); return; }
    const P1 = Pin.p;

    // ---- 第 1 次折射：空气(1) → 玻璃(1.5) ----
    const i1 = Math.acos(Math.min(1, Math.abs(_dt(_ml(nAB, -1), { x: 1, y: 0 }))));
    const dir2 = refractDir({ x: 1, y: 0 }, _ml(nAB, -1), 1.0, 1.5);
    if (!dir2) { ctx.restore(); return; }

    // ---- 棱镜内前进，求与右腰 AC 的真实交点 ----
    const hit2 = hitLine(P1, dir2, apex, br);
    if (!hit2) { ctx.restore(); return; }
    const P2 = hit2.p;

    // ---- 第 2 次折射：玻璃(1.5) → 空气(1) ----
    const cosI2 = Math.min(1, Math.abs(_dt(nAC, dir2)));
    const i2 = Math.acos(cosI2);
    const dir3 = refractDir(dir2, nAC, 1.5, 1.0);

    const rayC = '#e8862e';
    // 速度线所需：入射白光起点
    ctx.save();
    // ① 入射白光：沿水平方向画到左腰，末端落在棱镜表面
    drawArrow(ctx, wFrom.x, wFrom.y, P1.x, P1.y, rayC, false);
    // ② 棱镜内：沿**真实折射方向**画，终点就是真实出射点
    ctx.save();
    ctx.strokeStyle = rayC; ctx.lineWidth = 2.2;
    ctx.beginPath(); ctx.moveTo(P1.x, P1.y); ctx.lineTo(P2.x, P2.y); ctx.stroke();
    ctx.restore();
    // ③ 出射 7 色光：以真实净偏折角为中心展开
    const base = dir3 ? Math.atan2(dir3.y, dir3.x) : Math.atan2(dir2.y, dir2.x);
    const SPREAD = 5 * Math.PI / 180;               // 红光最小(-5°)、紫光最大(+5°)
    const LEN = 250;
    const ends = [];
    p.std.colors.forEach(function (col, i) {
      const t = i / (p.std.colors.length - 1);      // 0=红 … 1=紫
      const th = base - SPREAD + 2 * SPREAD * t;
      const ex = P2.x + LEN * Math.cos(th), ey = P2.y + LEN * Math.sin(th);
      ends.push({ x: ex, y: ey });
      drawArrow(ctx, P2.x, P2.y, ex, ey, col, false);
    });
    // ④ 入射点 / 出射点圆点（出射点现在真实落在右腰上）
    ctx.save();
    ctx.fillStyle = cssVar('--txt', '#17150e');
    [P1, P2].forEach(function (pt) {
      ctx.beginPath(); ctx.arc(pt.x, pt.y, 3.2, 0, Math.PI * 2); ctx.fill();
    });
    // 出射点加一圈高亮，提示"出射点在棱镜面上"
    ctx.strokeStyle = cssVar('--txt', '#17150e'); ctx.lineWidth = 1.2;
    ctx.beginPath(); ctx.arc(P2.x, P2.y, 6, 0, Math.PI * 2); ctx.stroke();
    ctx.restore();
    // ⑤ 两次折射的法线（虚线）+ 入射角 i₁ / 折射角 r₁ 标注
    ctx.save();
    const lineC = cssVar('--line', '#17150e');
    // 入射点法线（双向虚线，垂直左腰 = 沿 nAB）
    drawDashedLine(P1.x - nAB.x * 70, P1.y - nAB.y * 70,
                   P1.x + nAB.x * 70, P1.y + nAB.y * 70, lineC, [6, 5]);
    // 出射点法线（双向虚线，垂直右腰 = 沿 nAC）
    drawDashedLine(P2.x - nAC.x * 70, P2.y - nAC.y * 70,
                   P2.x + nAC.x * 70, P2.y + nAC.y * 70, lineC, [6, 5]);
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.fillStyle = cssVar('--muted2', '#3d3a2c');
    // 法线写"法线"二字，贴在虚线端点外侧
    ctx.fillText('法线', P1.x - nAB.x * 84, P1.y - nAB.y * 84 - 8);
    ctx.fillText('法线', P2.x + nAC.x * 84, P2.y + nAC.y * 84 + 10);
    // V4.9.12b：两次折射的角度数值移到左下空白区，用引线指到各自的折射点，
    //            避免压住出射光线（原先写在 P1/P2 右下会盖住彩虹扇面）
    const d2Deg = Math.atan2(dir2.y, dir2.x) * 180 / Math.PI;
    const d3Deg = dir3 ? Math.atan2(dir3.y, dir3.x) * 180 / Math.PI : d2Deg;
    const T1 = '① 进玻璃：偏向法线，转向底边  ' + d2Deg.toFixed(1) + '°';
    const T2 = '② 出玻璃：偏离法线，继续转向底边  ' + d3Deg.toFixed(1) + '°';
    const labelX = 18;
    const ly1 = P1.y + 74, ly2 = P1.y + 100;
    ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
    ctx.font = 'bold 12px sans-serif';
    // 引线：从标签右端连到对应折射点（浅色细线，不抢主体）
    ctx.save();
    ctx.strokeStyle = lineC; ctx.globalAlpha = 0.45; ctx.lineWidth = 1;
    ctx.beginPath(); ctx.moveTo(labelX + 4, ly1); ctx.lineTo(P1.x - 6, P1.y + 4); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(labelX + 4, ly2); ctx.lineTo(P2.x - 8, P2.y + 6); ctx.stroke();
    ctx.restore();
    ctx.fillStyle = cssVar('--txt', '#17150e');
    ctx.fillText(T1, labelX, ly1);
    ctx.fillText(T2, labelX, ly2);
    ctx.restore();
    // ⑥ 红上紫下的标注：贴在各自光线末端
    ctx.save();
    ctx.font = 'bold 12px sans-serif';
    ctx.textAlign = 'right'; ctx.textBaseline = 'middle';
    ctx.fillStyle = p.std.colors[0];
    ctx.fillText('红（偏折最小，在最上）', canvas.width - 10, ends[0].y);
    ctx.fillStyle = p.std.colors[p.std.colors.length - 1];
    ctx.fillText('紫（偏折最大，在最下）', canvas.width - 10,
                 ends[ends.length - 1].y);
    ctx.fillStyle = cssVar('--txt', '#17150e');
    ctx.font = 'bold 13px sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('白光 → 三棱镜 → 红橙黄绿蓝靛紫（7 色光）', canvas.width / 2, canvas.height - 22);
    ctx.restore();
    ctx.restore();
  }
  ctx.restore();
}

/* ===== V4.4 自由手绘交互（采点 → 平滑曲线） ===== */
let drawing = null;
function startDraw(e){
  if (!canvas || STATE.judging) return;
  e.preventDefault();
  const p = getPos(e);
  const tool = STATE.tool;
  if (tool === 'rainbow') {
    const n = STATE.strokes.filter(s => s.tool === 'rainbow').length;
    drawing = { tool: 'rainbow', color: RAINBOW[n % RAINBOW.length], points: [p] };
  } else {
    drawing = { tool: 'free', color: TOOL_COLORS[tool] || '#17150e', points: [p] };
  }
}
function moveDraw(e){
  if (!drawing) return;
  e.preventDefault();
  const p = getPos(e);
  const last = drawing.points[drawing.points.length - 1];
  if (Math.hypot(p.x - last.x, p.y - last.y) > 3) {
    drawing.points.push(p);
    drawScene(STATE.problem);
  }
}
function endDraw(e){
  if (!drawing) return;
  e.preventDefault();
  if (drawing.points.length >= 2) STATE.strokes.push(drawing);
  drawing = null;
  drawScene(STATE.problem);
}

function selectProblem(p){
  STATE.problem = p;
  STATE.strokes = [];
  STATE.undoStack = [];
  STATE.judgment = null;
  STATE.revealMode = false;
  STATE.pickAnswer = [];   // V4.9.6：pick/multi 题答案清零
  STATE.objAnswered = false;   // V4.10.1：新题解锁点选即判
  // 更新题库 UI
  document.querySelectorAll('.jp-item').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.jp-item[data-pid="' + escHtml(p.id) + '"]').forEach(el => el.classList.add('active'));
  // 更新提示
  const isObj = (p.type === 'pick' || p.type === 'multi');
  const tagText = (p.diff === 'basic' ? '基础' : p.diff === 'mid' ? '中等' : '进阶');
  // V4.9.9：p.name / p.promptHint 里的 "<" 必须转义（<b> 是我们自己写的标签，保留）
  const hintText = isObj
    ? '📌 <b>' + escHtml(p.name) + '</b>（' + tagText + '） · 单选题。' + escHtml(p.promptHint)
    : '📌 <b>' + escHtml(p.name) + '</b>（' + tagText + '） · ' + escHtml(p.promptHint);
  document.getElementById('judgeHint').innerHTML = hintText;
  // 清空结果
  document.getElementById('judgeResult').innerHTML = '<div class="jr-empty">' + (isObj ? '点击选项即可立即判对错' : '画完后点「📤 提交判卷」') + '</div>';
  // V4.9.11：revealMode 已复位，按钮文字必须跟着复位。
  //   原来只改 STATE 不改按钮文字——上一题看过答案后切到下一题，按钮还写着「🙈 隐藏答案」，
  //   但实际并未显示答案，点一下才"变成"隐藏，语义完全反了。
  document.getElementById('judgeReveal').textContent = '👁 查看标准答案';
  // V4.9.6：工具栏/题目区切换（客观题禁用画笔、显示选项）
  updateToolbarForType(p.type || 'trace');
  renderQuestionUI(p);
  if (window.AiLoading) window.AiLoading.hideAll();   // V4.8：切题时清理残留等待动画
  drawScene(p);
}

function selectTool(tool){
  STATE.tool = tool;
  document.querySelectorAll('.jt-btn[data-tool]').forEach(el => el.classList.remove('active'));
  document.querySelectorAll('.jt-btn[data-tool="' + tool + '"]').forEach(el => el.classList.add('active'));
}

function undoStroke(){
  STATE.strokes.pop();
  drawScene(STATE.problem);
}

function clearStrokes(){
  STATE.strokes = [];
  drawScene(STATE.problem);
}

function toggleReveal(){
  STATE.revealMode = !STATE.revealMode;
  document.getElementById('judgeReveal').textContent = STATE.revealMode ? '🙈 隐藏答案' : '👁 查看标准答案';
  const p = STATE.problem;
  // V4.9.11：客观题（pick/multi）的"标准答案"不走画布——drawScene 对客观题会提前 return，
  //   原来点「查看标准答案」只会把按钮文字改掉、画布上什么也不显示（= 用户看到的"点了没反应"）。
  //   现在改走 revealObjective()，把正确选项标出来并把解析写到判定区。
  if (p && (p.type === 'pick' || p.type === 'multi')) { revealObjective(p); return; }
  drawScene(p);
}

/* V4.9.11 新增：客观题的标准答案回显
   做两件事：① 在正确选项上挂一个「✓ 正确答案」徽标 + 解析；
            ② 在右侧判定区给出一份完整答案卡（正确答案 + 每个干扰项为什么错）。
   两处都只**新增/移除自己创建的元素**，不改动选项本身的 inline 样式——
   否则用户再点别的选项时，input 的 change 处理器会把这些样式一起清掉，状态就乱了。 */
function revealObjective(p){
  const wrap = document.querySelector('#tab-judge .canvas-wrap');
  const qcard = wrap ? wrap.querySelector('.qcard') : null;
  const show = STATE.revealMode;
  const correct = (p.options || []).filter(o => o.correct);
  if (qcard) {
    qcard.querySelectorAll('.qcard-opt').forEach(opt => {
      const o = (p.options || []).find(x => x.id === opt.dataset.oid);
      const old = opt.querySelector('.qcard-badge');
      const oldExp = opt.querySelector('.qcard-explain');
      if (old) old.remove();
      if (oldExp) oldExp.remove();
      if (!show || !o || !o.correct) return;
      // V4.10.1：已判卷的题选项上已挂 .qopt-badge（点选即判），不再重复挂徽标
      if (opt.querySelector('.qopt-badge')) return;
      const badge = document.createElement('span');
      badge.className = 'qcard-badge';
      badge.textContent = '✓ 正确答案';
      opt.appendChild(badge);
      if (o.explain) {
        const exp = document.createElement('div');
        exp.className = 'qcard-explain';
        exp.textContent = o.explain;
        opt.appendChild(exp);
      }
    });
  }
  const resEl = document.getElementById('judgeResult');
  if (!resEl) return;
  if (!show) {
    resEl.innerHTML = '<div class="jr-empty">选好答案后点「📤 提交判卷」</div>';
    return;
  }
  const rightTxt = correct.map(o => o.id + '. ' + o.text).join('；');
  const rows = (p.options || []).map(o =>
    '<li style="margin:4px 0;white-space:pre-wrap"><b>' + escHtml(o.id) + '.</b> ' + escHtml(o.text) + '　' +
    (o.correct ? '<b style="color:var(--green, #16a34a)">✓ 正确</b>' : '<span style="color:var(--muted)">✗ 错误</span>') +
    (o.explain ? '<br><span style="font-size:12px;color:var(--muted2)">' + escHtml(o.explain) + '</span>' : '') +
    '</li>'
  ).join('');
  resEl.innerHTML =
    '<div class="jr-card" style="padding:12px 14px;border-radius:10px;background:var(--verdict-bg);border:var(--hard-border);font-size:14px">' +
      '<div class="jr-head"><b>👁 标准答案</b> · 正确选项 <b style="color:var(--green, #16a34a);font-size:16px">' +
        escHtml(correct.map(o => o.id).join('')) + '</b></div>' +
      '<div style="margin-top:6px;line-height:1.6;font-size:13px">' + escHtml(rightTxt) + '</div>' +
      '<div style="margin-top:10px"><b style="font-size:12px;color:var(--muted)">📖 逐项解析：</b>' +
        '<ul style="margin:4px 0 0 18px;font-size:13px;line-height:1.5">' + rows + '</ul></div>' +
      '<div style="margin-top:8px;font-size:12px;color:var(--muted)">💡 ' + escHtml(p.promptHint) + '</div>' +
    '</div>';
}

/* ===== 4. 几何兜底算法（评审现场断网时使用） ===== */
function geometryJudge(p, strokes){
  const std = p.std;
  let total = 0, maxTotal = 0;
  const out = { scores: {}, highlights: [], notes: [] };

  if (p.id === 'reflect') {
    const incident = strokes.find(s => s.tool === 'incident');
    const normal = strokes.find(s => s.tool === 'normal');
    const reflect = strokes.find(s => s.tool === 'reflect');
    // angle
    maxTotal += 40;
    if (incident && normal) {
      const v1 = { x: incident.to.x - incident.from.x, y: incident.to.y - incident.from.y };
      const v2 = { x: normal.to.x - normal.from.x, y: normal.to.y - normal.from.y };
      const ang = Math.abs(angleBetween(v1, v2)) * 180 / Math.PI;
      const err = Math.abs(ang - std.incidentAngle);
      const sc = err <= 5 ? 40 : err <= 15 ? 20 : 0;
      out.scores.angle = { student: ang, error: err, score: sc };
      total += sc;
      if (incident) out.highlights.push({ type: 'line', from: incident.from, to: incident.to, ok: sc > 0 });
    } else { out.scores.angle = { score: 0 }; out.notes.push('未画入射光线或法线'); }
    // keypoint
    maxTotal += 30;
    if (incident) {
      const err = Math.hypot(incident.to.x - std.incidentPoint.x, incident.to.y - std.incidentPoint.y);
      const sc = err <= 20 ? 30 : err <= 50 ? 15 : 0;
      out.scores.keypoint = { error: err, score: sc };
      total += sc;
      out.highlights.push({ type: 'point', x: incident.to.x, y: incident.to.y, ok: sc >= 15 });
    } else { out.scores.keypoint = { score: 0 }; }
    // direction
    maxTotal += 20;
    if (incident && reflect && normal) {
      // 反射光线方向应与入射光线关于法线对称
      const vIn = unit({ x: incident.to.x - incident.from.x, y: incident.to.y - incident.from.y });
      const vRe = unit({ x: reflect.to.x - reflect.from.x, y: reflect.to.y - reflect.from.y });
      const vN = unit({ x: normal.to.x - normal.from.x, y: normal.to.y - normal.from.y });
      // 反射公式 v' = v - 2(v·n)n
      const dot = vIn.x * vN.x + vIn.y * vN.y;
      const vRefStd = { x: vIn.x - 2 * dot * vN.x, y: vIn.y - 2 * dot * vN.y };
      const cosA = vRe.x * vRefStd.x + vRe.y * vRefStd.y;
      const sc = cosA > 0.95 ? 20 : cosA > 0.85 ? 10 : 0;
      out.scores.direction = { correct: cosA > 0.95, score: sc };
      total += sc;
      out.highlights.push({ type: 'line', from: reflect.from, to: reflect.to, ok: sc >= 10 });
    } else { out.scores.direction = { score: 0, correct: false }; }
    // dashed
    maxTotal += 10;
    if (normal && normal.tool === 'normal') {
      out.scores.normal_dashed = { correct: true, score: 10 };
      total += 10;
    } else { out.scores.normal_dashed = { correct: false, score: 0 }; }
  }
  else if (p.id === 'mirror') {
    // 竖直镜面（x=500）：像与物左右对称，正立等大虚像
    const img = strokes.find(s => s.tool === 'reflect');  // 用 reflect 工具画像
    const mx = p.scene.mirror.x1;                          // 镜面 x
    const objX = p.scene.object.x;                         // 物 x
    maxTotal += 40;
    if (img) {
      // 对称性：像的 x 应接近镜像位置 2*mx - objX = 700
      const imgX = (img.from.x + img.to.x) / 2;
      const expectX = 2 * mx - objX;
      const err = Math.abs(imgX - expectX);
      const sc = err <= 15 ? 40 : err <= 35 ? 20 : 0;
      out.scores.symmetric = { error: err, score: sc };
      total += sc;
      // distance：像距 |imgX - mx| 应接近物距 |mx - objX| = 200
      const imgDist = Math.abs(imgX - mx), objDist = Math.abs(mx - objX);
      const dErr = Math.abs(imgDist - objDist);
      const dSc = dErr <= 10 ? 30 : dErr <= 25 ? 15 : 0;
      maxTotal += 30;
      out.scores.distance = { error: dErr, score: dSc };
      total += dSc;
      // upright：正立——像的 y 范围应与物接近（不上下翻转）
      const yErr = Math.abs(Math.min(img.from.y, img.to.y) - p.scene.object.y1) +
                   Math.abs(Math.max(img.from.y, img.to.y) - p.scene.object.y2);
      const uSc = yErr <= 30 ? 20 : yErr <= 60 ? 10 : 0;
      maxTotal += 20;
      out.scores.upright = { error: yErr, score: uSc };
      total += uSc;
      // 虚像
      maxTotal += 10;
      out.scores.virtual_dashed = { correct: true, score: 10 };
      total += 10;
      out.highlights.push({ type: 'line', from: img.from, to: img.to, ok: sc >= 20 });
    } else {
      out.scores.symmetric = { score: 0 };
      out.notes.push('未画像 A\'B\'（用「↗ 反射」工具画在镜面右侧）');
      maxTotal += 30 + 20 + 10;
      out.scores.distance = { score: 0 };
      out.scores.upright = { score: 0 };
      out.scores.virtual_dashed = { score: 0 };
    }
  }
  else if (p.id === 'lens') {
    // 凸透镜 u>2f：像在另一侧 x≈576（F' 540 与 2F' 620 之间），倒立实像
    const img = strokes.find(s => s.tool === 'reflect');
    const lensX = p.scene.lens.x, f = p.scene.f, axisY = p.scene.axis.y;
    const stdImg = p.std.imagePos;
    maxTotal += 40;
    if (img) {
      const imgX = (img.from.x + img.to.x) / 2;
      // imageInF2F：像应在 f<x- lens<2f 区间
      const vDist = imgX - lensX;
      const inRange = vDist > f && vDist < 2 * f;
      const err = Math.abs(imgX - stdImg.x);
      const sc = inRange ? (err <= 25 ? 40 : err <= 50 ? 25 : 15) : 0;
      out.scores.imageInF2F = { error: err, score: sc, studentV: Math.round(vDist) };
      total += sc;
      // inverted：倒立——像的顶端 y 应大于主光轴 y（在轴下方）
      const topY = Math.min(img.from.y, img.to.y), botY = Math.max(img.from.y, img.to.y);
      const invertedOK = topY >= axisY - 5;
      maxTotal += 25;
      out.scores.inverted = { correct: invertedOK, score: invertedOK ? 25 : 0 };
      total += invertedOK ? 25 : 0;
      // 实像实线
      maxTotal += 20;
      out.scores.real_solid = { correct: true, score: 20 };
      total += 20;
      // ratio：像高/物高 ≈ 0.44
      const objH = p.scene.object.y2 - p.scene.object.y1;  // 注意 y1<y2 存的是顶/底
      const imgH = Math.abs(botY - topY);
      const rErr = Math.abs(imgH / Math.abs(objH) - p.std.ratio);
      const rSc = rErr <= 0.1 ? 15 : rErr <= 0.2 ? 8 : 0;
      maxTotal += 15;
      out.scores.ratio = { error: rErr, score: rSc };
      total += rSc;
      out.highlights.push({ type: 'line', from: img.from, to: img.to, ok: sc >= 15 && invertedOK });
    } else {
      out.scores.imageInF2F = { score: 0 };
      out.notes.push('未画像（用「↗ 反射」工具画在凸透镜右侧）');
      maxTotal += 25 + 20 + 15;
      out.scores.inverted = { score: 0 };
      out.scores.real_solid = { score: 0 };
      out.scores.ratio = { score: 0 };
    }
  }
  else if (p.id === 'disperse') {
    // 色散：用 🌈 彩色笔画 7 色光谱线
    const lines = strokes.filter(s => s.tool === 'rainbow');
    maxTotal += 25;
    // colorCount
    const n = lines.length;
    const cSc = n >= 7 ? 25 : n >= 5 ? 18 : n >= 3 ? 10 : 0;
    out.scores.colorCount = { student: n, score: cSc };
    total += cSc;
    if (n >= 2) {
      // 按 y（起点）从上到下排序
      const sorted = lines.slice().sort((a, b) => Math.min(a.from.y, a.to.y) - Math.min(b.from.y, b.to.y));
      const idxs = sorted.map(s => RAINBOW.indexOf(s.color));
      // colorOrder：颜色索引序列应非递减（红上紫下）
      let inv = 0;
      for (let i = 1; i < idxs.length; i++) if (idxs[i] < idxs[i - 1]) inv++;
      const oSc = inv === 0 ? 30 : inv <= 2 ? 15 : 0;
      maxTotal += 30;
      out.scores.colorOrder = { inversions: inv, score: oSc };
      total += oSc;
      // redTop：最上面的线是红色
      const isRedTop = idxs[0] === 0;
      maxTotal += 25;
      out.scores.redTop = { correct: isRedTop, score: isRedTop ? 25 : 0 };
      total += isRedTop ? 25 : 0;
      // violetBottom：最下面的线是紫色
      const isVioletBot = idxs[idxs.length - 1] === 6;
      maxTotal += 20;
      out.scores.violetBottom = { correct: isVioletBot, score: isVioletBot ? 20 : 0 };
      total += isVioletBot ? 20 : 0;
      sorted.forEach(s => out.highlights.push({ type: 'line', from: s.from, to: s.to, ok: oSc >= 15 }));
    } else {
      out.notes.push('彩色光线太少（用「🌈 彩色」工具，每画一条自动换下一色）');
      maxTotal += 30 + 25 + 20;
      out.scores.colorOrder = { score: 0 };
      out.scores.redTop = { score: 0 };
      out.scores.violetBottom = { score: 0 };
    }
  }
  else {
    // 通用兜底：给基础分
    maxTotal = 100;
    total = strokes.length > 3 ? 60 : 30;
    out.scores.basic = { score: total };
    out.notes.push('离线模式：基础几何评估（具体维度评分需要 AI 模型）');
  }

  out.total = Math.round(total);
  out.maxTotal = maxTotal;
  out.model = 'geometry-fallback';
  return out;
}

function unit(v){ const l = Math.hypot(v.x, v.y); return { x: v.x / l, y: v.y / l }; }
function angleBetween(a, b){
  const dot = (a.x * b.x + a.y * b.y) / (Math.hypot(a.x, a.y) * Math.hypot(b.x, b.y));
  return Math.acos(Math.max(-1, Math.min(1, dot)));
}

/* ===== 5. AI 判卷（V4.4：手绘截图 → 多模态模型看图评分，3 次并发 + 评分卡） ===== */
async function aiJudge(p, strokes){
  // 手绘截图（整张答题画布，含场景与学生的彩色笔迹）
  const dataUrl = canvas.toDataURL('image/png');

  // 笔画统计（辅助信息：告诉模型学生用了哪几种颜色的笔画了几条）
  const colorStats = {};
  strokes.forEach(s => {
    const k = s.tool === 'rainbow' ? 'rainbow' : (Object.keys(TOOL_COLORS).find(k2 => TOOL_COLORS[k2] === s.color) || s.color);
    colorStats[k] = (colorStats[k] || 0) + 1;
  });

  const prompt = `你是一位耐心的初二物理教师，正在批改学生手绘的"${p.name}"光路图。

【题目要求】${p.promptHint}

【画面说明】
这是一张 ${canvas.width}×${canvas.height} 的答题画布截图。画布上已印有题目场景（深墨色结构线：镜面/主光轴/焦点标记/分界面/三棱镜/光源或物体，随题目而异）。学生用鼠标自由手绘了彩色笔迹，颜色约定：
- 红色 = 入射光线
- 蓝色 = 反射光线或像
- 绿色 = 折射光线
- 黑色 = 法线/辅助线
- 彩虹色（红橙黄绿蓝靛紫）= 色散光谱线
学生笔迹统计：${JSON.stringify(colorStats)}

【标准答案参数】
${JSON.stringify(p.std)}

【评判维度与权重】（总分 100）
${Object.entries(p.criteriaWeight).map(([k, w]) => '- ' + k + ': ' + w + ' 分').join('\n')}

请仔细看图，逐维度对照标准答案评分，并严格按以下 JSON 输出（不要任何额外文字、不要 markdown 代码块）：
{
  "scores": { ${p.criteria.map(c => '"' + c + '": {"score": <number 0-${p.criteriaWeight[c]}>}').join(', ')} },
  "total": <number 0-100>,
  "marks": [
    {"x": <0-1 相对横坐标>, "y": <0-1 相对纵坐标>, "ok": <true|false>, "label": "<≤8字，如：入射点正确/角度偏大>"}
  ],
  "diagnosis": "<50 字内、初二学生能听懂的诊断，先鼓励再指出问题>",
  "suggestions": ["<可操作改进建议1，≤40字>", "<建议2>"],
  "errorTypes": ["<错因归类：从下列固定标签中原样挑选 0~3 个 —— 概念理解错误 / 光路方向画反 / 角度偏差过大 / 法线未画或画成实线 / 虚实线不分 / 关键点位置偏移 / 箭头方向缺失 / 光线数量不足 / 颜色约定用错>"],
  "rootCause": "<60 字内：先说清错因属于哪一类，再说初二学生为什么会这样错，要指向具体认知难点，禁止泛泛而谈>",
  "variant": {"question": "<针对本题错因生成的一道同类变式题，≤60字>", "answer": "<该变式题的答案要点，≤40字>"}
}

要求：
1. marks 给 2~5 个关键判卷点（画对的地方 ok=true，画错/偏差的地方 ok=false）
2. diagnosis 必须包含至少一处鼓励 + 一处具体问题
3. 总分按各维度权重加权求和
4. 作图全对时：errorTypes 返回空数组 []，rootCause 写"无明显错因，作图规范"，variant 给一道同知识点的进阶变式题
5. 有错时：errorTypes 必须非空；rootCause 必须同时点出「错因类型」与「成因」，例如"折射角画得比入射角大——误以为光斜射入水中会远离法线，实际应靠近法线"
6. variant.question 必须与本题同知识点、同题型，只换数值或情境，不得直接重复本题`;

  // 3 次并发（同模型不同 temperature 模拟"多次判卷一致性对比"）
  const temperatures = [0.1, 0.3, 0.5];
  const rawReturns = [];   // V4.7：留存原始返回，解析全失败时用于诊断展示
  const results = await Promise.allSettled(
    temperatures.map((t, i) =>
      callVisionModel(prompt, dataUrl, t).then(r => { rawReturns.push(String(r || '')); return safeParseJSON(r); })
    )
  );

  const judgments = results
    .filter(r => r.status === 'fulfilled' && r.value)
    .map((r, i) => Object.assign({ _temperature: temperatures[i] }, r.value));

  if (judgments.length === 0) {
    console.warn('[judge] all vision AI runs failed');
    const netErr = results.find(r => r.status === 'rejected');
    if (netErr) throw new Error(netErr.reason ? netErr.reason.message : '网络请求失败');
    // 3 次都有返回但都解析不出 JSON —— 展示模型原始返回片段
    const lastRaw = rawReturns.length ? rawReturns[rawReturns.length - 1] : '(无返回)';
    throw new Error('3 次返回均无法解析为 JSON。模型原始返回片段：\n' +
      lastRaw.replace(/\s+/g, ' ').slice(0, 260) + '…');
  }

  // 评分卡：完整性(30%) + 一致性(40%) + 诊断质量(30%)
  // V4.9.14：模型被要求返回数字，但并不保证——若 total/score 是字符串，
  // reduce 的 a+b 会变成字符串拼接（"85"+"90"="8590"），均值/标准差全错、评分卡选错最佳判卷。
  // 统一先 Number 归一化，非有限数一律按 0 处理。
  const num = v => { const n = Number(v); return isFinite(n) ? n : 0; };
  const scored = judgments.map(j => {
    const completeness = (j.total !== undefined && j.diagnosis && j.suggestions && j.suggestions.length > 0) ? 100 : 50;
    const totals = judgments.map(x => num(x.total));
    const mean = totals.reduce((a, b) => a + b, 0) / totals.length;
    const stdDev = Math.sqrt(totals.reduce((s, t) => s + Math.pow(t - mean, 2), 0) / totals.length);
    const consistency = Math.max(0, 100 - stdDev * 2);
    const pedagogy = (j.diagnosis && /建议|可以|注意|试试|继续保持|不错/.test(j.diagnosis)) ? 100 : 60;
    const score = completeness * 0.3 + consistency * 0.4 + pedagogy * 0.3;
    return { judgment: j, score };
  });

  scored.sort((a, b) => b.score - a.score);
  const best = scored[0].judgment;
  best.model = 'run-t' + best._temperature;
  best.scoredDetails = scored;
  best.allJudgments = judgments;
  // V4.9.14：返回前把 total / scores.score 归一为数字——renderResult 与历史存储都按数字处理
  best.total = num(best.total);
  if (best.scores && typeof best.scores === 'object') {
    Object.keys(best.scores).forEach(k => {
      const v = best.scores[k];
      if (v && typeof v === 'object' && v.score !== undefined) v.score = num(v.score);
    });
  }

  let jc = getJudgeCfg();
  best.modelDisplay = jc.provider + ' · ' + (jc.model || '(默认视觉模型)');
  return best;
}

/* V4.4 判卷配置：独立于主 AI 设置（provider/model 可不同，key 留空复用主配置） */
function getJudgeCfg(){
  let jc = {}, main = {};
  try { jc = JSON.parse(localStorage.getItem('ai_optics_v1_judge') || '{}'); } catch (e) {}
  try { main = JSON.parse(localStorage.getItem('ai_optics_v1_cfg') || '{}'); } catch (e) {}
  const VISION_PROVIDERS = ['zhipu', 'minimax', 'kimi', 'openai', 'anthropic'];
  const mainP = VISION_PROVIDERS.indexOf(main.provider) >= 0 ? main.provider : 'zhipu';
  return {
    provider: jc.provider || mainP,
    model: jc.model || '',
    apikey: jc.apikey || main.apikey || '',
    baseUrl: jc.baseUrl || ''
  };
}

/* V4.4：多模态判卷调用——截图 base64 随 prompt 发给视觉模型 */
async function callVisionModel(prompt, dataUrl, temperature){
  const jc = getJudgeCfg();
  const PROVS = {
    zhipu:    { baseUrl: 'https://open.bigmodel.cn/api/paas/v4', chatPath: '/chat/completions', model: 'glm-5.3-flash' },
    minimax:  { baseUrl: 'https://api.minimaxi.com/v1',          chatPath: '/chat/completions', model: 'MiniMax-M3' },
    kimi:     { baseUrl: 'https://api.moonshot.cn/v1',           chatPath: '/chat/completions', model: 'moonshot-v1-8k-vision-preview' },
    openai:   { baseUrl: 'https://api.openai.com/v1',            chatPath: '/chat/completions', model: 'gpt-4o' },
    anthropic:{ baseUrl: 'https://api.anthropic.com',            chatPath: '/v1/messages',      model: 'claude-haiku-4-5' }
  };
  const d = PROVS[jc.provider];
  if (!d) throw new Error('判卷 Provider 无效：' + jc.provider + '（请在「⚖ 判卷模型设置」中选择）');
  if (!jc.apikey) throw new Error('未配置 API Key——请打开「⚖ 判卷模型设置」填写，或在顶部「⚙ AI 设置」配置主 Key');
  const baseUrl = jc.baseUrl || d.baseUrl;
  const model = jc.model || d.model;

  const sysMsg = '你是初中物理（光学）AI 判卷教师，严格基于苏科版2024新教材。你会看到一张学生手绘光路图的画布截图。'
    + '除逐维度评分外，你还必须完成【错因归因】——判断错在哪一类、为什么会错，并据此生成一道同类变式题。'
    + '只输出严格 JSON，无任何额外文字。';
  let headers, body;
  // V4.7：noThink——GLM/M3 系列默认可能输出思考过程导致 JSON 解析失败，显式关闭
  const NO_THINK = ['zhipu', 'minimax', 'kimi'];
  if (jc.provider === 'anthropic') {
    headers = { 'x-api-key': jc.apikey, 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json' };
    body = JSON.stringify({
      model, max_tokens: 2000, system: sysMsg, temperature: temperature,
      messages: [{ role: 'user', content: [
        { type: 'image', source: { type: 'base64', media_type: 'image/png', data: dataUrl.split(',')[1] } },
        { type: 'text', text: prompt }
      ]}]
    });
  } else {
    // OpenAI 兼容多模态格式（zhipu GLM 多模态 / MiniMax-M3 / Kimi 视觉版 / GPT-4o 均适用）
    headers = { 'Authorization': 'Bearer ' + jc.apikey, 'Content-Type': 'application/json' };
    const obj = {
      model, temperature: temperature, max_tokens: 2000,
      messages: [
        { role: 'system', content: sysMsg },
        { role: 'user', content: [
          { type: 'text', text: prompt },
          { type: 'image_url', image_url: { url: dataUrl } }
        ]}
      ]
    };
    if (NO_THINK.indexOf(jc.provider) >= 0) obj.thinking = { type: 'disabled' };   // V4.7
    body = JSON.stringify(obj);
  }
  const res = await fetch(baseUrl + d.chatPath, { method: 'POST', headers, body });
  if (!res.ok) {
    const t = await res.text();
    throw new Error('HTTP ' + res.status + ': ' + t.slice(0, 160));
  }
  const data = await res.json();
  if (jc.provider === 'anthropic') {
    const blocks = data.content || [];
    return (blocks.find(b => b.type === 'text') || {}).text || '';
  }
  return (data.choices && data.choices[0] && data.choices[0].message && data.choices[0].message.content) || '';
}

function safeParseJSON(s){
  if (!s) return null;
  let cleaned = String(s).trim();
  // V4.7：剥思考过程标签（GLM/M3 可能输出 <think>…</think>）
  cleaned = cleaned.replace(/<think>[\s\S]*?<\/think>/gi, '').trim();
  // 剥 markdown 代码块
  const cm = cleaned.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (cm) cleaned = cm[1].trim();
  try { return JSON.parse(cleaned); } catch (e) {}
  // V4.7 宽容提取：模型可能在 JSON 前后说了话——取首个 { 到最后一个 } 之间的块
  const p1 = cleaned.indexOf('{'), p2 = cleaned.lastIndexOf('}');
  if (p1 >= 0 && p2 > p1) {
    const block = cleaned.slice(p1, p2 + 1);
    try { return JSON.parse(block); } catch (e) {}
    // 常见尾逗号修复：{"a":1,} / [1,2,]
    try { return JSON.parse(block.replace(/,(\s*[}\]])/g, '$1')); } catch (e) {}
  }
  console.warn('[judge] JSON parse failed:', String(s).slice(0, 200));
  return null;
}

/* ===== 6. 判卷结果回显 ===== */
/* V4.9.9 安全加固：本函数回显的是**外部 LLM 返回的文本**（model / modelDisplay / error / student /
   diagnosis / suggestions），是全站最高风险的一处 innerHTML。模型偶尔会吐出含 <、>、& 的内容
   （例如「∵∠1<∠2」、「φ>90°」），未转义时会被浏览器解析成标签，轻则样式错乱、重则吞掉后面的
   兄弟节点（V4.9.7 题库被吞 7 题就是同一类问题）。以下所有变量都过 escHtml()。
   注意：class 名 cls/cls2、数字 total/sc 是程序自己算的，不需要也不应转义。 */
function renderResult(judgment){
  const el = document.getElementById('judgeResult');
  if (window.AiLoading) window.AiLoading.hide(el);   // V4.8：终止判卷等待动画
  // V4.9.14：total/score 强制按数字取值（aiJudge 已归一化，这里再兜底一次，杜绝字符串进模板）
  const total = Number(judgment.total) || 0;
  const cls = total >= 80 ? 'jr-ok' : total >= 60 ? 'jr-mid' : 'jr-bad';
  const modelLabel = judgment.model === 'geometry-fallback'
    ? '📐 几何兜底（AI 不可用）'
    : '🤖 AI 评卷 · ' + escHtml(judgment.model || 'kimi-k3');
  // V4.9.9：modelDisplay 是厂家给的展示名，照样过转义
  const modelDisplay = escHtml(judgment.modelDisplay || '');

  let rows = '';
  if (judgment.scores) {
    Object.entries(judgment.scores).forEach(([k, v]) => {
      const sc = Number(v && v.score) || 0;   // V4.9.14：防 null/字符串
      const cls2 = sc >= 80 ? 'jr-ok' : sc >= 50 ? 'jr-mid' : 'jr-bad';
      const extra = (v && v.error !== undefined) ? ` (误差 ${typeof v.error === 'number' ? v.error.toFixed(1) : escHtml(v.error)})` : '';
      const extra2 = (v && v.student !== undefined) ? ` 学生值 ${typeof v.student === 'number' ? v.student.toFixed(1) : escHtml(v.student)}` : '';
      rows += `<div class="jr-row"><span class="jr-name">${escHtml(criterionName(k))}${extra2}${extra}</span><span class="jr-score ${cls2}">${sc}</span></div>`;
    });
  }

  // 3 次对比表（同模型不同 temperature）
  let compareHTML = '';
  if (judgment.allJudgments && judgment.allJudgments.length > 1) {
    compareHTML = '<div style="margin-top:10px;padding:8px;background:#f3f4f6;border-radius:6px;font-size:11px"><b>🆚 3 次并发判卷（温度 0.1/0.3/0.5）：</b><br>';
    judgment.allJudgments.forEach(j => {
      compareHTML += `· t=${escHtml(j._temperature)} → 总分 ${escHtml(j.total || '?')}<br>`;
    });
    compareHTML += `→ 选中 <b>t=${escHtml(bestRunTemperature(judgment))}</b>（评分卡最优）</div>`;
  }

  // V4.9.9：诊断/建议是模型自由文本，转义后用 pre-wrap 保住它自己的换行与缩进
  const diag = judgment.diagnosis
    ? `<div class="jr-diag">📝 <b>诊断：</b><span style="white-space:pre-wrap">${escHtml(judgment.diagnosis)}</span></div>` : '';
  const sug = judgment.suggestions && judgment.suggestions.length
    ? `<div class="jr-sug">💡 <b>建议：</b><ul>${judgment.suggestions.map(s => '<li style="white-space:pre-wrap">' + escHtml(s) + '</li>').join('')}</ul></div>` : '';

  // V5.1.0：错因归因（错误类型标签 + 根因解释 + 同类变式题）
  // 安全：errorTypes / rootCause / variant 全部来自外部 LLM，一律过 escHtml
  let causeHTML = '';
  const ets = Array.isArray(judgment.errorTypes) ? judgment.errorTypes.filter(Boolean) : [];
  const rc = judgment.rootCause ? String(judgment.rootCause) : '';
  const vr = (judgment.variant && typeof judgment.variant === 'object') ? judgment.variant : null;
  if (ets.length || rc || vr) {
    causeHTML = '<div class="jr-cause">🔍 <b>错因归因：</b>';
    if (ets.length) {
      causeHTML += '<div class="jr-cause-tags">' +
        ets.map(t => '<span class="jr-cause-tag">' + escHtml(t) + '</span>').join('') + '</div>';
    }
    if (rc) causeHTML += '<div style="white-space:pre-wrap;margin-top:6px">' + escHtml(rc) + '</div>';
    if (vr && (vr.question || vr.answer)) {
      causeHTML += '<div class="jr-variant"><b>🧩 同类变式练一练：</b>'
        + (vr.question ? '<div style="white-space:pre-wrap;margin-top:4px">' + escHtml(vr.question) + '</div>' : '')
        + (vr.answer ? '<details style="margin-top:6px"><summary style="cursor:pointer;color:var(--muted)">查看答案要点</summary>'
            + '<div style="white-space:pre-wrap;margin-top:4px">' + escHtml(vr.answer) + '</div></details>' : '')
        + '</div>';
    }
    causeHTML += '</div>';
  }

  el.innerHTML = `
    <div class="jr-total ${cls}">${total}<span style="font-size:18px;color:#9ca3af"> / 100</span></div>
    <div class="jr-model">${modelLabel} · <span style="color:#9ca3af">${modelDisplay}</span></div>
    ${rows}
    ${diag}
    ${causeHTML}
    ${sug}
    ${compareHTML}
  `;

  // V4.8.1：判卷结果入场动画（总分 → 各维度行 → 诊断/建议 → 对比表 依次浮现）
  try {
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (window.gsap && !reduce && el.children.length) {
      gsap.from(el.children, {
        autoAlpha: 0, y: 10, duration: 0.38, ease: 'power2.out',
        stagger: 0.06, overwrite: 'auto', clearProps: 'transform'
      });
    }
  } catch (e) {}
}

function criterionName(k){
  const map = {
    angle: '角度精度', keypoint: '关键点位置', direction: '反射方向',
    normal_dashed: '法线虚实线', symmetric: '对称性', distance: '距离相等',
    upright: '正立', virtual_dashed: '虚线虚像',
    imageInF2F: '像在 f~2f', inverted: '倒立', real_solid: '实像实线', ratio: '缩放比',
    refractAngle: '折射角', refractColor: '折射颜色', normalBoth: '两侧法线',
    incident: '入射光线', colorCount: '颜色数量', colorOrder: '颜色顺序',
    redTop: '红光在上', violetBottom: '紫光在下', basic: '基础评估'
  };
  return map[k] || k;
}

function bestRunTemperature(judgment){
  if (judgment.scoredDetails && judgment.scoredDetails[0]) {
    return judgment.scoredDetails[0].judgment._temperature;
  }
  return '?';
}

/* ===== V4.6：GSAP AI 等待动画模块（挂全局，供 v4.2 闭包内 runChat/runDiag/诊断弹窗使用）
   V4.8：加 _active 注册表 + hideAll()——支持"追加式"等待容器，safeRender 统杀全部动画 ===== */
window.AiLoading = (function(){
  const reduceMotion = (function(){
    try { return window.matchMedia('(prefers-reduced-motion: reduce)').matches; } catch (e) { return false; }
  })();
  let active = [];   // 所有正在播放动画的元素
  function show(el, text){
    if (!el) return;
    if (!window.gsap || reduceMotion) { el.textContent = text || '…'; try{ el.setAttribute('aria-busy','true'); }catch(e){} return; }
    hide(el);
    el.innerHTML = '<span class="ail-dots"><i></i><i></i><i></i></span><span class="ail-text"></span><span class="ail-sweep"></span>';
    el.classList.add('ai-loading');
    el.querySelector('.ail-text').textContent = text || '';
    // 三点波浪：back.out 弹跳 + 错峰 stagger + yoyo 循环
    const tw = gsap.timeline({ repeat: -1 });
    tw.fromTo(el.querySelectorAll('.ail-dots i'),
        { y: 0, scale: 0.55, opacity: 0.45 },
        { y: -8, scale: 1.2, opacity: 1, duration: 0.42, ease: 'back.out(2.2)', stagger: 0.14, yoyo: true, repeat: -1 }, 0)
      // 呼吸光晕：accent 色 boxShadow 脉冲
      .fromTo(el,
        { boxShadow: '0 0 0px 0px rgba(200,240,79,0)' },
        { boxShadow: '0 0 16px 3px rgba(200,240,79,.45)', duration: 0.85, ease: 'sine.inOut', yoyo: true, repeat: -1 }, 0)
      // 文字淡入
      .fromTo(el.querySelector('.ail-text'), { autoAlpha: 0, x: -6 }, { autoAlpha: 1, x: 0, duration: 0.35, ease: 'power2.out' }, 0.1);
    el._ailTween = tw;
    if (active.indexOf(el) < 0) active.push(el);
    // V4.9：等待期间置 aria-busy，抑制读屏逐帧播报；渲染完成由 safeRender 解除后统一朗读
    try{ el.setAttribute('aria-busy', 'true'); }catch(e){}
  }
  function hide(el){
    if (el && el._ailTween) { el._ailTween.kill(); el._ailTween = null; }
    if (el) {
      el.classList.remove('ai-loading');
      const i = active.indexOf(el);
      if (i >= 0) active.splice(i, 1);
      try{ el.setAttribute('aria-busy', 'false'); }catch(e){}
    }
  }
  /* V4.8：终止所有活跃等待动画（safeRender 等"回答渲染"必经点调用，杜绝泄漏） */
  function hideAll(){
    active.slice().forEach(function(el){ hide(el); });
  }
  return { show: show, hide: hide, hideAll: hideAll };
})();

/* V4.5：判卷历史存储（per 学生，供 v4.2 闭包内诊断 prompt 读取） */
function saveJudgeHistory(p, result){
  try {
    let stu = null;
    try { stu = JSON.parse(localStorage.getItem('ai_optics_v1_curstu') || 'null'); } catch (e) {}
    const key = 'ai_optics_v1_judgehist' + (stu ? '_' + stu.id : '');
    let hist = [];
    try { hist = JSON.parse(localStorage.getItem(key) || '[]'); } catch (e) {}
    hist.push({
      t: Date.now(),
      pid: p.id, pname: p.name,
      total: result.total || 0,
      scores: result.scores || {},
      diagnosis: result.diagnosis || '',
      suggestions: result.suggestions || []
    });
    if (hist.length > 50) hist = hist.slice(-50);
    localStorage.setItem(key, JSON.stringify(hist));
  } catch (e) { console.warn('[judge] save history failed:', e); }
}

/* ===== 7. 提交判卷（V4.4：AI 不可用时明确提示，不再几何硬凑） ===== */
async function submitJudge(){
  if (!STATE.problem) { alert('请先选一道题'); return; }
  if (STATE.judging) return;
  // V4.9.6：客观题（pick/multi）路由
  const p = STATE.problem;
  if(p.type === 'pick' || p.type === 'multi'){
    // V4.10.1：选择题已由「点选即判」接管，此分支仅作兜底（按钮平时已禁用）
    if (STATE.objAnswered) return;
    if(!STATE.pickAnswer || STATE.pickAnswer.length === 0){ alert('请先选答案'); return; }
    STATE.judging = true;
    const resEl = document.getElementById('judgeResult');
    resEl.innerHTML = '<div class="jr-loading">判卷中…</div>';
    try{
      const result = objectiveJudge(p, STATE.pickAnswer);
      result.scoredDetails = [{ judgment: result, score: 100 }];
      result.allJudgments = [result];
      result.modelDisplay = '本地客观题判卷（瞬间）';
      STATE.judgment = result;
      saveJudgeHistory(p, result);   // V4.5：入判卷历史
      renderObjectiveResult(p, result);
      recordSess(result.total === 100);   // V4.10.0：计入本次练习统计
    }catch(e){
      console.error('[judge obj] error:', e);
      // V4.9.14：与 V4.9.9 收口原则一致——异常文本必须转义后再入 innerHTML
      resEl.innerHTML = '<div class="jr-empty">判卷失败：' + escHtml(e && e.message ? e.message : '未知') + '</div>';
    }
    STATE.judging = false;
    return;
  }
  // 手绘题（trace）原逻辑保留
  if (STATE.strokes.length === 0) { alert('画布为空，请先手绘光路'); return; }
  STATE.judging = true;
  // V4.8：判卷等待也使用统一 GSAP 动画
  const resEl = document.getElementById('judgeResult');
  if (window.AiLoading) { window.AiLoading.show(resEl, 'AI 正在看图判卷（3 次并发）'); }
  else { resEl.innerHTML = '<div class="jr-loading">AI 正在看图判卷（3 次并发）</div>'; }
  try {
    const result = await aiJudge(STATE.problem, STATE.strokes);
    STATE.judgment = result;
    saveJudgeHistory(STATE.problem, result);   // V4.5：入判卷历史，供「诊断」结合画图反馈
    renderResult(result);
    drawScene(STATE.problem);  // 重绘画布：笔迹 + marks 标注
  } catch (e) {
    console.error('[judge] error:', e);
    if (window.AiLoading) window.AiLoading.hideAll();   // V4.8：失败也清理动画
    // V4.9.9：e.message 里可能裹着模型原始返回片段（含 < > &），必须转义；
    // 原样保留 \n + white-space:pre-wrap，保证多行报错排版不变
    document.getElementById('judgeResult').innerHTML =
      '<div class="jr-empty" style="text-align:left;white-space:pre-wrap;line-height:1.7">⚠️ AI 判卷不可用\n<span style="color:var(--red);font-size:12px">' +
      escHtml(e && e.message ? e.message : '未知错误') +
      '</span>\n<span style="font-size:12px">可在「⚖ 判卷模型设置」里点「🧪 测试连接」排查</span></div>';
  }
  STATE.judging = false;
}

/* ===== V4.4 判卷模型设置弹窗 ===== */
function openJudgeCfg(){
  const jc = getJudgeCfg();
  document.getElementById('jcProvider').value = jc.provider;
  document.getElementById('jcModel').value = jc.model || '';
  // 安全：不回显任何 key（判卷专属 key 存过则提示已设置）
  const judgeKeySet = (function(){ try { const j = JSON.parse(localStorage.getItem('ai_optics_v1_judge') || '{}'); return !!(j.apikey); } catch (e) { return false; } })();
  const keyInput = document.getElementById('jcKey');
  keyInput.value = '';
  keyInput.placeholder = judgeKeySet ? '已设置判卷专属 Key（留空保持不变）' : '留空 = 复用主 AI 设置的 Key';
  document.getElementById('jcBaseUrl').value = jc.baseUrl || '';
  document.getElementById('judgeCfgMask').classList.add('show');
}
function closeJudgeCfg(){
  document.getElementById('judgeCfgMask').classList.remove('show');
}
function saveJudgeCfg(){
  const provider = document.getElementById('jcProvider').value;
  const model = document.getElementById('jcModel').value.trim();
  const apikey = document.getElementById('jcKey').value.trim();
  const baseUrl = document.getElementById('jcBaseUrl').value.trim();
  let prev = {};
  try { prev = JSON.parse(localStorage.getItem('ai_optics_v1_judge') || '{}'); } catch (e) {}
  const next = { provider, model, baseUrl };
  if (apikey) next.apikey = apikey;           // 留空 = 保持之前的（或无，fallback 主 key）
  else if (prev.apikey) next.apikey = prev.apikey;
  try { localStorage.setItem('ai_optics_v1_judge', JSON.stringify(next)); } catch (e) {}
  closeJudgeCfg();
  // 更新提交按钮提示（让用户知道当前判卷模型）
  document.getElementById('judgeSubmit').textContent = '📤 提交判卷（' + provider + ' · ' + (model || '默认视觉模型') + '）';
}

/* V4.7：测试连接——用 1x1 小图 + 极简 JSON 指令做全链路验证（表单当前值即时生效） */
const TINY_PNG = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=';
async function testJudgeCfg(){
  const out = document.getElementById('jcTestResult');
  out.style.display = 'block';
  out.textContent = '⏳ 测试中…（发送 1x1 测试图 + 极简 JSON 指令，走完整判卷链路）';
  try {
    // 先把表单当前值写入 localStorage，让 callVisionModel 立即使用
    const provider = document.getElementById('jcProvider').value;
    const model = document.getElementById('jcModel').value.trim();
    const apikey = document.getElementById('jcKey').value.trim();
    const baseUrl = document.getElementById('jcBaseUrl').value.trim();
    let prev = {};
    try { prev = JSON.parse(localStorage.getItem('ai_optics_v1_judge') || '{}'); } catch (e) {}
    const next = { provider, model, baseUrl };
    if (apikey) next.apikey = apikey; else if (prev.apikey) next.apikey = prev.apikey;
    try { localStorage.setItem('ai_optics_v1_judge', JSON.stringify(next)); } catch (e) {}

    const raw = await callVisionModel('这张图是一张纯色测试图。请只输出严格 JSON：{"ok":true}，不要任何其他文字。', TINY_PNG, 0.1);
    const parsed = safeParseJSON(raw);
    if (parsed) {
      out.textContent = '✅ 连接成功！模型可正常输出 JSON。\n模型返回：' + String(raw).replace(/\s+/g, ' ').slice(0, 160);
    } else {
      out.textContent = '⚠️ 模型有响应但无法解析为 JSON（判卷也会遇到同样问题）。\n原始返回：' + String(raw).replace(/\s+/g, ' ').slice(0, 240);
    }
  } catch (e) {
    out.textContent = '❌ 测试失败：' + (e && e.message ? e.message : e);
  }
}

/* ===== 8. 题库 UI 渲染 ===== */
// V4.10.0：题库分类过滤——'all' | 'pick'（选择题） | 'trace'（作图题）
let JCAT = 'all';
function renderProblemList(){
  const el = document.getElementById('judgeProblemList');
  if (!el) return;
  // V4.9.7：用 HTML 转义防止 promptHint/question 中的 <、>、& 被解析成标签
  //（典型 case：lens 的 promptHint 含 "f<v<2f"，原版会让浏览器把后续题吞进 <v> 标签里）
  // V4.9.9：局部 escHtml 已删除，统一改用顶层 escHtml()
  const list = PROBLEMS.filter(p => JCAT === 'all' ? true
    : (JCAT === 'pick' ? (p.type === 'pick' || p.type === 'multi') : p.type === 'trace'));
  el.innerHTML = list.map(p => {
    // V4.9.6：题型标签 + 客观题题干截断到 30 字
    const typeTag = (p.type === 'pick' || p.type === 'multi') ? '单选' : '手绘';
    const hint = (p.type === 'pick' || p.type === 'multi') ? p.question : p.promptHint;
    return `
    <div class="jp-item" data-pid="${p.id}">
      <b>${escHtml(p.name)}</b>
      <span class="jp-diff ${p.diff}">${p.diff === 'basic' ? '基础' : p.diff === 'mid' ? '中等' : '进阶'}</span>
      <span class="jp-type">${typeTag}</span>
      <div class="jp-hint">${escHtml(hint)}</div>
    </div>`;
  }).join('');
  el.querySelectorAll('.jp-item').forEach((el2) => {
    el2.addEventListener('click', (e) => {
      e.stopPropagation();
      const target = e.currentTarget;
      const p = PROBLEMS.find(x => x.id === target.dataset.pid);
      if (p) selectProblem(p);
    });
  });
}

/* ===== V4.10.0：题库分类入口 / 随机出题 / 本次练习统计 ===== */
// 本次会话统计：进入挑战页才开始计时；只在页面内存中（刷新即清零，符合"本次"语义）
// V5.0.2：新增 paused / pausedAt / elapsedBefore 支持暂停/继续
const SESS = { start: null, paused: false, pausedAt: null, elapsedBefore: 0, answered: 0, correct: 0 };
function recordSess(isRight){
  SESS.answered++;
  if (isRight) SESS.correct++;
  renderSessStats();
}
/* V5.0.2：暂停/继续本次练习计时
   关键不变量：elapsedBefore 永远是"已确认的实际训练时长"，暂停期间不累加。
   - 暂停：把当前段 [start, now] 累加到 elapsedBefore，然后清空 start，记录 pausedAt
   - 继续：清空 pausedAt，重设 start=now（新段开始）；elapsedBefore 不动
   这样 renderSessStats 计算 elapsed = paused ? elapsedBefore : elapsedBefore + (now - start) 即可 */
function toggleSessPause(){
  if (SESS.paused){
    // 继续：清空 pausedAt，新开一段；elapsedBefore 不动
    SESS.pausedAt = null;
    SESS.paused = false;
    SESS.start = Date.now();
  } else {
    // 暂停：把当前段累加到 elapsedBefore，再冻结
    if (SESS.start != null) SESS.elapsedBefore += Date.now() - SESS.start;
    SESS.start = null;
    SESS.paused = true;
    SESS.pausedAt = Date.now();
  }
  renderSessStats();
}
function renderSessStats(){
  const el = document.getElementById('judgeSessionStats');
  if (!el) return;
  // V5.0.2：暂停时不累加，按 elapsedBefore + (now - start) 计算
  const now = Date.now();
  const elapsed = SESS.paused
    ? SESS.elapsedBefore
    : SESS.elapsedBefore + (SESS.start ? now - SESS.start : 0);
  let line = (SESS.paused ? '⏸ 已暂停 ' : '⏱ 本次已练 ') + fmtSessDur(elapsed);
  if (SESS.answered > 0){
    const rate = Math.round(SESS.correct * 100 / SESS.answered);
    line += ' ｜ 已答 ' + SESS.answered + ' 题 · 答对 ' + SESS.correct + ' · 正确率 ' + rate + '%';
  } else {
    line += ' ｜ 选择题未开始作答';
  }
  el.textContent = line;
  // V5.0.2：同步暂停按钮的文本/样式
  const pb = document.getElementById('judgePause');
  if (pb){
    pb.textContent = SESS.paused ? '▶ 继续计时' : '⏸ 暂停计时';
    pb.classList.toggle('active', SESS.paused);
  }
}
function fmtSessDur(ms){
  const s = Math.max(0, Math.floor(ms / 1000));
  const m = Math.floor(s / 60), r = s % 60;
  return (m < 10 ? '0' : '') + m + ':' + (r < 10 ? '0' : '') + r;
}
// 计时心跳：仅当挑战页可见时才起算与刷新（切走时冻结时长）
// V5.0.2：暂停时（pausedAt != null）跳过 SESS.start 设置，保持冻结
setInterval(function(){
  try{
    const tab = document.getElementById('tab-judge');
    if (tab && tab.classList.contains('active')){
      if (!SESS.start && !SESS.pausedAt) SESS.start = Date.now();
      renderSessStats();
    }
  }catch(e){}
}, 1000);

function initJudgeCatBar(){
  const bar = document.getElementById('judgeCatBar');
  if (!bar) return;
  bar.querySelectorAll('.jcat-btn[data-cat]').forEach(b => {
    b.addEventListener('click', () => {
      JCAT = b.dataset.cat;
      bar.querySelectorAll('.jcat-btn[data-cat]').forEach(x => x.classList.toggle('active', x === b));
      renderProblemList();
    });
  });
  const rand = document.getElementById('judgeRandom');
  if (rand) rand.addEventListener('click', () => {
    gotoRandomPick(STATE.problem && STATE.problem.id);
  });
  // V5.0.2：暂停/继续本次练习计时
  const pauseBtn = document.getElementById('judgePause');
  if (pauseBtn) pauseBtn.addEventListener('click', toggleSessPause);
  renderSessStats();
}

// V4.10.2：从选择题池随机跳一题（排除 excludeId）——随机按钮与"答完自动切题"共用
function gotoRandomPick(excludeId){
  const pool = PROBLEMS.filter(p => p.type === 'pick' && p.id !== excludeId);
  if (!pool.length) return;
  selectProblem(pool[Math.floor(Math.random() * pool.length)]);
}

/* ===== V4.9.6：客观题（pick/multi）UI + 判卷 ===== */
// 切换工具栏：trace 显示画笔，pick/multi 禁用画笔
function updateToolbarForType(type){
  const jt = document.querySelector('.judge-toolbar');
  if(!jt) return;
  const isObj = (type === 'pick' || type === 'multi');
  jt.style.opacity = isObj ? '0.35' : '1';
  jt.style.pointerEvents = isObj ? 'none' : 'auto';
  // 撤销/清空 在客观题下也禁用
  const undo = document.getElementById('judgeUndo');
  const clearBtn = document.getElementById('judgeClear');
  if(undo) undo.disabled = isObj;
  if(clearBtn) clearBtn.disabled = isObj;
  // 揭示答案 文字改
  const rev = document.getElementById('judgeReveal');
  if(rev && isObj) rev.textContent = '👁 查看标准答案';
  // V4.10.1：选择题点选即判，提交按钮禁用（防重复计分）；手绘题恢复
  const sb = document.getElementById('judgeSubmit');
  if(sb) sb.disabled = isObj;
}

// 渲染客观题的题目+选项到 .canvas-wrap 区域（替换 canvas 显示）
function renderQuestionUI(p){
  const wrap = document.querySelector('#tab-judge .canvas-wrap');
  if(!wrap) return;
  const isObj = (p.type === 'pick' || p.type === 'multi');
  const cv = document.getElementById('cv-judge');
  const overlay = document.getElementById('judgeOverlay');
  let qcard = wrap.querySelector('.qcard');
  if(!isObj){
    // 手绘题：恢复 canvas 显示、移除 qcard
    if(cv) cv.style.display = '';
    if(overlay) overlay.style.display = '';
    if(qcard) qcard.style.display = 'none';
    return;
  }
  // 客观题：用题干+选项卡片覆盖画布
  if(!cv || !overlay) return;
  cv.style.display = 'none';
  overlay.style.display = 'none';
  // 检查是否已有 question-card（qcard 已在函数顶部声明过）
  if(!qcard){
    qcard = document.createElement('div');
    qcard.className = 'qcard';
    qcard.style.cssText = 'background:var(--sec-bg);border:var(--hard-border);border-radius:12px;padding:20px 24px;min-height:480px;font-size:15px;line-height:1.7;color:var(--txt);';
    wrap.appendChild(qcard);
  }
  qcard.style.display = 'block';
  // V4.10.4：选项顺序随机（修复 V4.10.0 题库答案集中在 A 位置的隐患——30+ 道单选题
  //   几乎全部把正确答案排在 A 位置，学生只要"无脑选 A"就能答对，违背考查目的）。
  //   Fisher-Yates 洗牌 + 重新分配 A/B/C/D id。直接修改 p.options 数组本身和元素 id，
  //   下游 answerObjective / objectiveJudge / revealObjective 都通过 p.options 访问
  //   （find / filter），自动跟随新顺序，零侵入。
  //   每次 selectProblem → renderQuestionUI 都会重新洗牌，所以同一题每次进入选项位置
  //   都不同，进一步打消"靠记忆位置答题"的侥幸。
  if (Array.isArray(p.options) && p.options.length > 1){
    const _ids = ['A','B','C','D'];
    const _arr = p.options;
    for (let _i = _arr.length - 1; _i > 0; _i--){
      const _j = Math.floor(Math.random() * (_i + 1));
      const _t = _arr[_i]; _arr[_i] = _arr[_j]; _arr[_j] = _t;
    }
    _arr.forEach((_o, _k) => { _o.id = _ids[_k] || _o.id; });
  }
  // V4.9.8：题库已全为单选题，标签固定为「单选」
  const optTag = '单选';
  // V4.9.9 安全加固：题干 / 选项 id / 选项文字 / 提示语全部过 escHtml()。
  // 这些目前是开发者手写的题库常量（内容可信），但其中含 "f<v<2f"、"φ>θ" 这类**数学小于号**，
  // 不转义就会被浏览器当标签解析（同 V4.9.7 事故）。转义同时也让以后引入外部题库源时天然安全。
  qcard.innerHTML = `
    <div style="font-size:12px;color:var(--muted);margin-bottom:6px">📚 ${optTag}题 · ${p.diff === 'basic' ? '基础' : p.diff === 'mid' ? '中等' : '进阶'}</div>
    <div style="font-size:18px;font-weight:700;margin-bottom:18px;line-height:1.55">${escHtml(p.question)}</div>
    <div class="qcard-opts" style="display:flex;flex-direction:column;gap:10px">
      ${p.options.map(o => `
        <label class="qcard-opt" data-oid="${escHtml(o.id)}" style="display:flex;align-items:flex-start;gap:12px;padding:12px 14px;border:2px solid var(--line);border-radius:10px;cursor:pointer;background:var(--panel);transition:all .15s">
          <input type="radio" name="qopt-${escHtml(p.id)}" value="${escHtml(o.id)}" style="margin-top:4px;flex-shrink:0">
          <span style="flex:1"><b style="margin-right:6px">${escHtml(o.id)}.</b>${escHtml(o.text)}</span>
        </label>
      `).join('')}
    </div>
    <div style="margin-top:14px;font-size:12px;color:var(--muted)">${escHtml(p.promptHint)}</div>
  `;
  qcard.querySelectorAll('.qcard-opt').forEach(opt => {
    const inp = opt.querySelector('input');
    // V4.10.1：点选即判——change 触发 answerObjective（自动判卷 + 计分 + 全屏对勾/红叉）
    inp.addEventListener('change', () => {
      if (STATE.objAnswered) return;          // 已判卷锁定，忽略后续选择
      const oid = opt.dataset.oid;
      STATE.pickAnswer = [oid];
      answerObjective(p, oid);
    });
    // 点击 label 区域也要响应
    opt.addEventListener('click', (e) => {
      if (STATE.objAnswered) return;
      if(e.target.tagName !== 'INPUT'){
        // 在 label 区域点击 → 切换 input
        inp.checked = !inp.checked;
        inp.dispatchEvent(new Event('change'));
      }
    });
  });
  // V4.10.1：答题卡「逐段浮现」入场动画（与知识地图 kd-anim 同款节奏：元信息→题干→选项块→提示）
  // 随机一题/切题走同一路径（selectProblem → renderQuestionUI），动画自动复用
  try{
    const reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (window.gsap && !reduce && qcard.children.length){
      gsap.from(qcard.children, {
        autoAlpha: 0, y: 14,
        duration: 0.34, ease: 'power2.out',
        stagger: 0.07, overwrite: 'auto', clearProps: 'transform'
      });
    }
  }catch(e){}
}

/* ===== V4.10.1：选择题点选即判（自动判卷 + 锁定 + 全屏对勾/红叉反馈） ===== */
function answerObjective(p, oid){
  if (STATE.objAnswered) return;
  STATE.objAnswered = true;
  const result = objectiveJudge(p, [oid]);
  result.scoredDetails = [{ judgment: result, score: 100 }];
  result.allJudgments = [result];
  result.modelDisplay = '本地判卷（瞬间）';
  STATE.judgment = result;
  saveJudgeHistory(p, result);   // 入判卷历史（AI 诊断会统计选择题目对情况）
  renderObjectiveResult(p, result);
  recordSess(result.total === 100);   // 计入本次练习统计
  // 选项锁定 + 对错标记：正确项标绿挂「正确答案」，选错的项标红挂「你选的」
  const wrap = document.querySelector('#tab-judge .canvas-wrap');
  const qcard = wrap ? wrap.querySelector('.qcard') : null;
  if (qcard){
    const optsEl = qcard.querySelector('.qcard-opts');
    if (optsEl) optsEl.classList.add('locked');
    qcard.querySelectorAll('.qcard-opt').forEach(o2 => {
      const o = (p.options || []).find(x => x.id === o2.dataset.oid);
      if (o && o.correct){
        o2.classList.add('chosen-right');
        appendOptBadge(o2, '✓ 正确答案', 'right');
      } else if (o && o.id === oid && !o.correct){
        o2.classList.add('chosen-wrong');
        appendOptBadge(o2, '✗ 你选的', 'wrong');
      }
    });
  }
  // V4.10.2：对错图标播完（约 3 秒后消失）→ 自动切到下一道选择题。
  // 仅当用户仍停留在本题时才切（若手动换题/切 tab 则不接管）
  const answeredPid = p.id;
  showResultMark(result.total === 100, function(){
    if (STATE.problem && STATE.problem.id === answeredPid) gotoRandomPick(answeredPid);
  });
}
function appendOptBadge(opt, text, cls){
  const b = document.createElement('span');
  b.className = 'qopt-badge ' + cls;
  b.textContent = text;
  opt.appendChild(b);
}
// 全屏 3D 对勾/红叉：弹出（back.out）→ 描边生长 → 轻微晃动 → 停留 → 淡出移除，全程约 3 秒
// V4.10.2：onDone 在图标完全消失后回调（供自动切下一题）
function showResultMark(ok, onDone){
  const ov = document.createElement('div');
  ov.className = 'mark-overlay';
  const c = ok ? '#16a34a' : '#dc2626';
  const fill = ok ? 'rgba(22,163,74,.10)' : 'rgba(220,38,38,.10)';
  const glyph = ok
    ? '<circle cx="100" cy="100" r="88" fill="'+fill+'" stroke="'+c+'" stroke-width="8"/>'+
      '<path d="M55 104 L90 140 L150 68" fill="none" stroke="'+c+'" stroke-width="20" stroke-linecap="round" stroke-linejoin="round"/>'
    : '<circle cx="100" cy="100" r="88" fill="'+fill+'" stroke="'+c+'" stroke-width="8"/>'+
      '<path d="M66 66 L134 134" fill="none" stroke="'+c+'" stroke-width="20" stroke-linecap="round"/>'+
      '<path d="M134 66 L66 134" fill="none" stroke="'+c+'" stroke-width="20" stroke-linecap="round"/>';
  ov.innerHTML = '<svg viewBox="0 0 200 200" aria-hidden="true">'+glyph+'</svg>';
  document.body.appendChild(ov);
  const done = () => { try{ ov.remove(); }catch(e){} if (typeof onDone === 'function') onDone(); };
  let reduce = false;
  try{ reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches; }catch(e){}
  if (window.gsap && !reduce){
    const paths = ov.querySelectorAll('path');
    paths.forEach(p => {
      try{ const len = p.getTotalLength(); p.style.strokeDasharray = len; p.style.strokeDashoffset = len; }catch(e){}
    });
    gsap.timeline({ onComplete: done })
      .from(ov.firstElementChild, { scale: .4, autoAlpha: 0, duration: .4, ease: 'back.out(2.2)' })
      .to(paths, { strokeDashoffset: 0, duration: .45, stagger: .12, ease: 'power2.out' }, '-=0.15')
      .to(ov.firstElementChild, { rotation: ok ? 4 : -4, duration: .09, repeat: 3, yoyo: true, ease: 'sine.inOut' })
      .to(ov.firstElementChild, { autoAlpha: 0, scale: .85, duration: .55, ease: 'power1.in', delay: 1.1 });
  } else {
    setTimeout(() => {
      ov.style.transition = 'opacity .6s';
      ov.style.opacity = '0';
      setTimeout(done, 650);
    }, 1800);
  }
}

// 客观题判卷（pick/multi）——纯本地，瞬间返回
function objectiveJudge(p, answer){
  const correctIds = p.options.filter(o => o.correct).map(o => o.id);
  const correctSet = new Set(correctIds);
  const ansSet = new Set(answer || []);
  const tp = (p.options || []).length;
  const fp = (answer || []).length - correctIds.filter(x => ansSet.has(x)).length;
  const fn = correctIds.length - correctIds.filter(x => ansSet.has(x)).length;
  const total = correctIds.length;
  const hit = correctIds.filter(x => ansSet.has(x)).length;
  // 评分：选对一项 +100/total；选错一项 -50/total（不出现负分，加 0 下限）
  let score = Math.max(0, Math.round((hit - fp) * (100 / Math.max(1, total))));
  // 单选场景特殊处理：选对=100，选错=0
  if(!p.multi && tp > 0){
    score = ansSet.size === 1 && correctSet.has([...ansSet][0]) ? 100 : 0;
  }
  // V4.9.8：题库全为单选，反馈话术按单选口径给出（不再出现"漏选/错选几项"）
  const isSingle = !p.multi && tp > 0;
  const allRight = hit === total && fp === 0;
  let diag;
  if (allRight) {
    diag = '✓ 完全正确！' + p.options.filter(o => o.correct)
      .map(o => '「' + o.text + '」' + (o.explain ? '：' + o.explain : '')).join('；');
  } else if (isSingle) {
    const chosen = (answer || [])[0];
    const chosenOpt = p.options.find(o => o.id === chosen);
    diag = '× 答错了。你选的是「' + (chosenOpt ? chosenOpt.text : '（未选）') + '」'
         + (chosenOpt && chosenOpt.explain ? '——' + chosenOpt.explain : '')
         + ' 正确答案是「' + (p.options.find(o => o.correct) || {}).text + '」。';
  } else if (hit > 0) {
    diag = '部分正确。答对 ' + hit + ' / ' + total + ' 项；漏选 ' + fn + ' 项' + (fp > 0 ? '，错选 ' + fp + ' 项' : '') + '。';
  } else {
    diag = '× 全部错误。';
  }
  return {
    total: score,
    scores: { answer: { score, correct: allRight, hit, miss: fn, wrong: fp } },
    correctIds,
    userAnswer: answer || [],
    model: 'objective-local',
    diagnosis: diag,
    suggestions: p.options.filter(o => o.correct && (!answer || !answer.includes(o.id)))
      .slice(0, 3).map(o => '「' + o.text + '」' + (o.explain ? '：' + o.explain : ''))
  };
}

// 客观题结果渲染
// V4.9.9 安全加固：diagnosis / suggestions 里拼进了**选项原文**（可能含 < > 符号），全部转义后再入 innerHTML
function renderObjectiveResult(p, judgment){
  const resEl = document.getElementById('judgeResult');
  const ok = judgment.total === 100;
  const tag = ok ? '🎉 完全正确' : (judgment.total >= 60 ? '👍 部分正确' : '💪 再想想');
  const head = `<div class="jr-head"><b>${tag}</b> · 得分 <b style="color:${ok ? 'var(--green, #16a34a)' : 'var(--red)'};font-size:18px">${judgment.total}</b> / 100</div>`;
  const explain = `<div style="margin-top:8px;line-height:1.6;font-size:13px;white-space:pre-wrap">${escHtml(judgment.diagnosis)}</div>`;
  let sug = '';
  if(judgment.suggestions && judgment.suggestions.length){
    sug = '<div style="margin-top:8px"><b style="font-size:12px;color:var(--muted)">📚 需要补的：</b><ul style="margin:4px 0 0 18px;font-size:13px;line-height:1.55">' +
      judgment.suggestions.map(s => '<li style="white-space:pre-wrap">' + escHtml(s) + '</li>').join('') + '</ul></div>';
  }
  resEl.innerHTML = `<div class="jr-card" style="padding:12px 14px;border-radius:10px;background:var(--verdict-bg);border:var(--hard-border);font-size:14px">${head}${explain}${sug}</div>`;
}

/* ===== 9. 初始化 ===== */
function init(){
  if (!canvas) return;  // 当前 tab 未激活
  // 工具栏
  document.querySelectorAll('.jt-btn[data-tool]').forEach(el => {
    el.addEventListener('click', () => selectTool(el.dataset.tool));
  });
  document.getElementById('judgeUndo').addEventListener('click', undoStroke);
  document.getElementById('judgeClear').addEventListener('click', clearStrokes);
  document.getElementById('judgeSubmit').addEventListener('click', submitJudge);
  document.getElementById('judgeReveal').addEventListener('click', toggleReveal);
  // V4.4 判卷模型设置弹窗
  document.getElementById('judgeCfgBtn').addEventListener('click', openJudgeCfg);
  document.getElementById('judgeCfgSave').addEventListener('click', saveJudgeCfg);
  document.getElementById('judgeCfgTest').addEventListener('click', testJudgeCfg);
  document.getElementById('judgeCfgClose').addEventListener('click', closeJudgeCfg);
  document.getElementById('judgeCfgMask').addEventListener('click', e => { if (e.target.id === 'judgeCfgMask') closeJudgeCfg(); });
  // Canvas 鼠标
  canvas.addEventListener('mousedown', startDraw);
  canvas.addEventListener('mousemove', moveDraw);
  canvas.addEventListener('mouseup', endDraw);
  canvas.addEventListener('mouseleave', () => { drawing = null; });
  // 触屏
  canvas.addEventListener('touchstart', startDraw, { passive: false });
  canvas.addEventListener('touchmove', moveDraw, { passive: false });
  canvas.addEventListener('touchend', endDraw, { passive: false });
  // 键盘 Ctrl+Z
  document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'z' && document.getElementById('tab-judge').classList.contains('active')) {
      undoStroke();
    }
  });
  // 题库
  renderProblemList();
  initJudgeCatBar();   // V4.10.0：分类入口 + 随机出题 + 本次统计
  // 默认选第一题
  selectProblem(PROBLEMS[0]);
  // 提交按钮显示当前判卷模型
  try {
    const jc = getJudgeCfg();
    document.getElementById('judgeSubmit').textContent = '📤 提交判卷（' + jc.provider + ' · ' + (jc.model || '默认视觉模型') + '）';
  } catch (e) {}
  // 主题切换时重绘画布（跟随 V4.2 亮/深主题）
  try {
    new MutationObserver(() => drawScene(STATE.problem)).observe(document.body, { attributes: true, attributeFilter: ['class'] });
  } catch (e) {}
}

// 初始化（V4.4 修复：只跑一次，防 init+tryInit 双重绑定）
let _judgeInited = false;
function bootInit(){
  if (_judgeInited || !document.getElementById('tab-judge')) return;
  _judgeInited = true;
  init();
  // V4.9.1：向健壮性兜底模块报告「已成功启动」。此后偶发异常不再弹全屏浮层（避免打断课堂使用）。
  try { window.__APP_READY = true; } catch (e) {}
}
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', bootInit);
} else {
  setTimeout(bootInit, 100);
}

})();
