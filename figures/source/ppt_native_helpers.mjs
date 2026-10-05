import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
import {Path2D} from '@napi-rs/canvas';
import {Presentation, PresentationFile} from '@oai/artifact-tool';
export const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
export const style = JSON.parse(await fs.readFile(path.join(root,'figures/ppt_style.json'),'utf8'));
export const SKILL_DIR=process.env.FAIREDA_PRESENTATION_SKILL_DIR ?? 'presentations';
export const inch=value=>value*96;
export function createFigure(widthIn=7,heightIn=4){
  const presentation=Presentation.create({slideSize:{width:inch(widthIn),height:inch(heightIn)}});
  const slide=presentation.slides.add(); slide.background.fill='#FFFFFF';
  return {presentation,slide,widthIn,heightIn};
}
export function text(slide,value,x,y,w,h=20,options={}){
  const shape=slide.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  shape.text=String(value);
  shape.text.style={typeface:style.font,fontSize:(options.pt??9)*96/72,color:options.color??'#000000',bold:options.bold??false,autoFit:'none',...options};
  shape.text.insets={left:0,right:0,top:0,bottom:0};
  return shape;
}
export function rect(slide,x,y,w,h,fill='none',stroke='#000000',width=.7){return slide.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width}});}
export function rounded(slide,x,y,w,h,fill='#FFFFFF',stroke='#0072B2',radius=7){return slide.shapes.add({geometry:'roundRect',borderRadius:radius,position:{left:x,top:y,width:w,height:h},fill,line:{fill:stroke,width:.65}});}
export function polyline(slide,points,color='#000000',width=1,dash='solid'){
  const minX=Math.min(...points.map(point=>point[0])), minY=Math.min(...points.map(point=>point[1]));
  const spanX=Math.max(0.01,Math.max(...points.map(point=>point[0]))-minX),spanY=Math.max(0.01,Math.max(...points.map(point=>point[1]))-minY);
  return slide.shapes.add({geometry:'custom',position:{left:minX,top:minY,width:spanX,height:spanY},fill:'none',line:{fill:color,width,style:dash},customPaths:[{width:spanX,height:spanY,commands:points.map((point,index)=>({[index?'lineTo':'moveTo']:{x:point[0]-minX,y:point[1]-minY}}))}]});
}
export const line=(slide,x1,y1,x2,y2,color='#000000',width=1,dash='solid')=>polyline(slide,[[x1,y1],[x2,y2]],color,width,dash);
export function marker(slide,x,y,color='#000000',radius=2,kind='circle'){
  if(kind==='cross'){line(slide,x-radius,y-radius,x+radius,y+radius,color);return line(slide,x-radius,y+radius,x+radius,y-radius,color);}
  if(kind==='diamond')return polyline(slide,[[x,y-radius],[x+radius,y],[x,y+radius],[x-radius,y],[x,y-radius]],color,.8);
  return slide.shapes.add({geometry:kind==='square'?'rect':'ellipse',position:{left:x-radius,top:y-radius,width:2*radius,height:2*radius},fill:'#FFFFFF',line:{fill:color,width:.8}});
}
export const panel=(slide,label,title,x,y,w)=>text(slide,`${label}  ${title}`,x,y,w,23,{bold:true});
export function arrow(slide,x1,y1,x2,y2,color='#000000',width=1){line(slide,x1,y1,x2,y2,color,width);const angle=Math.atan2(y2-y1,x2-x1);for(const offset of [-.5,.5])line(slide,x2,y2,x2-5*Math.cos(angle+offset),y2-5*Math.sin(angle+offset),color,width);}
export async function icon(slide,name,x,y,size=24,color='#000000'){
  const directory=path.join(root,'figures/assets/official_feather');
  const source=await fs.readFile(path.join(directory,`${name}.svg`),'utf8');
  const manifest=JSON.parse(await fs.readFile(path.join(directory,'manifest.json'),'utf8'));
  if(createHash('sha256').update(source).digest('hex')!==manifest.find(entry=>entry.name===name).sha256)throw new Error(`Official icon hash mismatch: ${name}`);
  const draw=points=>polyline(slide,points.map(point=>[x+point[0]*size/24,y+point[1]*size/24]),color,1);
  for(const element of source.matchAll(/<(path|rect|circle|ellipse|line|polyline|polygon)\s+([^>]+)\/>/g)){
    const attrs=Object.fromEntries([...element[2].matchAll(/([\w-]+)="([^"]*)"/g)].map(match=>[match[1],match[2]]));
    const value=key=>Number(attrs[key]||0);
    const geometry=new Path2D(element[1]==='path'?attrs.d:undefined);
    if(element[1]==='rect')geometry.roundRect(value('x'),value('y'),value('width'),value('height'),value('rx'));
    if(element[1]==='circle')geometry.arc(value('cx'),value('cy'),value('r'),0,Math.PI*2);
    if(element[1]==='ellipse')geometry.ellipse(value('cx'),value('cy'),value('rx'),value('ry'),0,0,Math.PI*2);
    if(element[1]==='line'){geometry.moveTo(value('x1'),value('y1'));geometry.lineTo(value('x2'),value('y2'));}
    if(['polyline','polygon'].includes(element[1])){
      const numbers=attrs.points.trim().split(/[ ,]+/).map(Number);
      for(let index=0;index<numbers.length;index+=2)geometry[index?'lineTo':'moveTo'](numbers[index],numbers[index+1]);
      if(element[1]==='polygon')geometry.closePath();
    }
    let points=[];
    for(const segment of geometry.toSVGString().matchAll(/([MLQCZ])([^MLQCZ]*)/g)){
      const values=(segment[2].match(/[-+]?(?:\d*\.\d+|\d+)(?:e[-+]?\d+)?/gi)||[]).map(Number);
      if(segment[1]==='M'){if(points.length)draw(points);points=[values];}
      else if(segment[1]==='L')points.push(values);
      else if(segment[1]==='Z')points.push(points[0]);
      else{
        const start=points.at(-1);
        for(let step=1;step<=12;step++){
          const fraction=step/12,complement=1-fraction;
          points.push([0,1].map(axis=>segment[1]==='Q'?complement**2*start[axis]+2*complement*fraction*values[axis]+fraction**2*values[axis+2]:complement**3*start[axis]+3*complement**2*fraction*values[axis]+3*complement*fraction**2*values[axis+2]+fraction**3*values[axis+4]));
        }
      }
    }
    if(points.length)draw(points);
  }
}
export async function finalizeFigure(figure,name,notes=''){
  if(!process.env.RUNTIME_NODE_MODULES) throw new Error('Set RUNTIME_NODE_MODULES before rebuilding schematics.');
  const build=path.join(root,'figures/.build',name,String(Date.now()));await fs.mkdir(build,{recursive:true});
  figure.slide.speakerNotes.textFrame.setText(notes);
  const candidatePath=path.join(build,'candidate.pptx');await(await PresentationFile.exportPptx(figure.presentation)).save(candidatePath);
  const {finalizePresentation}=await import(`${SKILL_DIR}/container_tools/artifact_tool_utils.mjs`);
  const canonicalPath=path.join(root,'figures/editable',`${name}.pptx`);
  let finalPath=canonicalPath;
  try{await fs.access(canonicalPath);await fs.mkdir(path.join(build,'revisions'),{recursive:true});finalPath=path.join(build,'revisions',`revision-${Date.now()}.pptx`);}catch{}
  const pythonExecutable=process.env.FAIREDA_PYTHON ?? 'python3';
  const soffice=process.env.FAIREDA_SOFFICE ?? 'soffice';
  await finalizePresentation({workspaceDir:root,candidatePath,finalPath,pythonExecutable,integrityValidatorPath:`${SKILL_DIR}/container_tools/inspect_presentation_package_integrity.py`,layoutValidatorPath:`${SKILL_DIR}/container_tools/inspect_presentation_layout_geometry.py`,layoutArgs:['--expected-slide-size-emu',`${Math.round(figure.widthIn*914400)},${Math.round(figure.heightIn*914400)}`],explicitTotalSlideCount:1,fontPolicy:{basis:'user_request',families:[style.font]},verifyArtifactToolImport:true,receiptPath:path.join(build,'validation.json')});
  if(finalPath!==canonicalPath)await fs.copyFile(finalPath,canonicalPath);
  execFileSync(soffice,[`-env:UserInstallation=file://${build}/office`,'--headless','--convert-to','pdf','--outdir',path.join(root,'figures','editable'),canonicalPath],{timeout:120000,env:{...process.env}});
  return canonicalPath;
}
