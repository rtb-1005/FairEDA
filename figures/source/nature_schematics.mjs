// Native, editable study-design and network figures; no statistical computation.
import fs from 'node:fs/promises';
import path from 'node:path';
import { createFigure, text, rounded, line, polyline, arrow, finalizeFigure, root, style } from './ppt_native_helpers.mjs';

// In-memory setting for these two builds only; the historical style file is unchanged.
style.font = 'Arial';
const ink = '#303030', edge = '#8C969C', blue = '#0072B2', orange = '#D55E00';
const fills = { neutral: '#F4F6F7', blue: '#EAF3F7', warm: '#FFF0E4', white: '#FFFFFF' };
function tx(slide, value, x, y, w, h=15, options={}) {
  return text(slide, value, x, y, w, h, {pt:7, color:ink, ...options});
}
function card(slide, x, y, w, h, lines, tone='white') {
  rounded(slide,x,y,w,h,fills[tone],tone==='warm'?orange:edge,3);
  const step = 13;
  const total = lines.length*step;
  lines.forEach((value,i)=>tx(slide,value,x+7,y+(h-total)/2+i*step,w-14,14,
    {pt:lines.length>3?6.4:(i===0?7.2:6.8),bold:i===0}));
}
function label(slide, letter, title, x, y, width) {
  tx(slide,letter,x,y,12,15,{pt:8,bold:true});tx(slide,title,x+18,y+1,width-18,15);
}
function connect(slide, points, color=ink) {
  polyline(slide,points,color,.65);
  const last=points.length-1;arrow(slide,...points[last-1],...points[last],color,.65);
}

function design() {
  const f=createFigure(7,2.9),s=f.slide;
  rounded(s,14,27,644,78,'#F7FAFB','#D6E1E6',4);
  rounded(s,14,116,644,105,'#FAFAF9','#E0E2E3',4);
  label(s,'a','SOURCE · supervised reference evaluation',24,30,620);
  card(s,24,45,150,51,['EDABE source','43 records · 128 Hz','Raw + expert-clean','Point-wise labels'],'blue');
  card(s,198,45,101,51,['Fixed split','33 train','10 test']);
  card(s,325,45,131,51,['Frozen checkpoints','CRG-A / CRG-B','Distinct weights'],'warm');
  card(s,484,45,163,51,['Reference diagnostics','Out-of-fold + test']);
  for(const [x1,x2] of [[174,198],[299,325],[456,484]])arrow(s,x1,70.5,x2,70.5,ink,.7);
  label(s,'b','TARGET · downstream task evaluation',24,119,620);
  card(s,24,144,151,62,['VR balance task','11 participants','984 windows · 58.8 Hz','720 samples / window'],'blue');
  card(s,213,144,128,30,['Raw input']);
  card(s,213,183,128,37,['CRG-B gate','Frozen transfer'],'warm');
  connect(s,[[175,175],[193,175],[193,159],[213,159]]);
  connect(s,[[193,175],[193,201],[213,201]]);
  card(s,379,150,158,54,['Matched 11-fold LOSO','10 train / 1 held out','Same folds for both arms']);
  connect(s,[[341,159],[359,159],[359,168],[379,168]]);
  connect(s,[[341,201],[359,201],[359,186],[379,186]]);
  card(s,571,142,76,68,['catch22 + RF','HYDRA','MiniRocket','MultiRocket','ROCKET']);
  arrow(s,537,177,571,177,ink,.7);
  tx(s,'Task inference: seeds 1005 / 2004 / 2027 · participant-cluster bootstrap (20,000 replicates); seeds averaged within replicate.',24,232,626,14,{pt:6.4});
  tx(s,'Expert-clean reference labels are unavailable in the target corpus.',24,251,626,12,{pt:6.4,color:orange});
  return f;
}

function network() {
  const f=createFigure(7,3.0),s=f.slide;
  tx(s,'Frozen residual-gated operator',16,7,635,15,{pt:8.2,bold:true});
  card(s,16,63,78,44,['Raw EDA','x'],'blue');
  card(s,109,57,96,56,['Normalize','x / scale'],'blue');
  card(s,221,63,82,44,['Stem','48 channels']);
  card(s,320,49,107,72,['Residual trunk','9 blocks · 48 channels','Dilations 1, 2, 4, 8, 16,','32, 64, 128, 256']);
  arrow(s,94,85,109,85,ink,.75);
  arrow(s,205,85,221,85,ink,.75);
  arrow(s,303,85,320,85,ink,.75);
  card(s,447,39,100,42,['Probability head','p = σ(logit)'],'blue');
  card(s,447,93,100,42,['Residual head','r = 4 tanh(d)'],'warm');
  connect(s,[[427,85],[436,85],[436,60],[447,60]]);
  connect(s,[[436,85],[436,114],[447,114]]);
  card(s,568,63,80,44,['Gate','p × r']);
  connect(s,[[547,60],[557,60],[557,77],[568,77]],blue);
  connect(s,[[547,114],[557,114],[557,92],[568,92]],orange);

  card(s,16,163,168,49,['Robust scale','max(P95(raw) − P5(raw),','0.05 µS)']);
  connect(s,[[55,107],[55,146],[55,163]],blue);
  card(s,264,163,174,49,['Normalized residual','max(x + p·r, 0)']);
  connect(s,[[157,113],[157,145],[250,145],[250,188],[264,188]],blue);
  tx(s,'normalized skip x',170,132,95,11,{pt:6.1,color:blue});
  connect(s,[[608,107],[608,145],[351,145],[351,163]],ink);
  card(s,490,163,158,49,['Output','residual × scale'],'blue');
  connect(s,[[184,188],[218,188],[218,238],[569,238],[569,212]],edge);
  tx(s,'scale path',226,240,75,11,{pt:6.1,color:edge});
  arrow(s,438,188,490,188,ink,.75);
  tx(s,'Receptive field: 4089 samples ≈ 32 s at 128 Hz; VR input uses 58.8 Hz.',16,261,638,14,{pt:6.4});
  return f;
}

const choices={4:['fig04_design',design],5:['fig05_network',network]};
for(const id of (process.argv.slice(2).length?process.argv.slice(2).map(Number):[4,5])){
  const [name,builder]=choices[id];
  const caption=await fs.readFile(path.join(root,'figures',`${name}.caption.md`),'utf8');
  await finalizeFigure(builder(),name,`${caption}\nNative editable shapes; Arial, 6.5–7 pt labels and 8 pt panel letters. White background, minimal fills, no icons or decorative ruler. Original scientific labels and separate CRG-A / CRG-B identities retained.`);
  await fs.copyFile(path.join(root,'figures','editable',`${name}.pdf`),path.join(root,'paper','figures',`${name}.pdf`));
  console.log(`${name}: native Nature-style schematic complete`);
}
