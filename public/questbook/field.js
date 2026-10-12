'use strict';

// A native WebGL instrument; quest controls remain ordinary, accessible HTML.
window.QuestField = class QuestField {
  constructor(canvas, onProject) {
    Object.assign(this, { canvas, onProject, time: 0, yaw: -.12, pitch: .12,
      distance: 8.8, active: true, sound: false, selected: -1, pulse: -100,
      pointer: [.5,.5], pointers: new Map(), anchors: [], frameId: null, lastFrame: 0 });
    this.paused = matchMedia('(prefers-reduced-motion: reduce)').matches;
    try {
      this.gl = canvas.getContext('webgl', {alpha:false,antialias:false,powerPreference:'low-power'});
      if(!this.gl) throw new Error('WebGL unavailable');
      this.setup();
      document.documentElement.dataset.renderer = 'webgl';
    } catch {
      this.gl = null;
      document.documentElement.dataset.renderer = 'fallback';
    }
    this.bindInput();
    this.resizeObserver = new ResizeObserver(()=>this.resize());
    this.resizeObserver.observe(canvas);
    document.addEventListener('visibilitychange',()=>{
      if(document.hidden&&this.audio) this.audio.suspend().catch(()=>{});
      this.requestFrame();
    });
  }

  program(vertex, fragment) {
    const gl = this.gl;
    const shaders = [[gl.VERTEX_SHADER,vertex],[gl.FRAGMENT_SHADER,fragment]].map(([type,source])=>{
      const shader=gl.createShader(type);
      gl.shaderSource(shader,source);
      gl.compileShader(shader);
      if(!gl.getShaderParameter(shader,gl.COMPILE_STATUS)) throw new Error('Shader unavailable');
      return shader;
    });
    const program=gl.createProgram();
    shaders.forEach(shader=>gl.attachShader(program,shader));
    gl.linkProgram(program);
    if(!gl.getProgramParameter(program,gl.LINK_STATUS)) throw new Error('Renderer unavailable');
    shaders.forEach(shader=>gl.deleteShader(shader));
    return program;
  }

  setup() {
    const gl=this.gl;
    this.background=this.program(`
      attribute vec2 a_position;
      varying vec2 v_uv;
      void main(){v_uv=a_position*.5+.5;gl_Position=vec4(a_position,0.,1.);}
    `, `
      precision mediump float;
      varying vec2 v_uv;
      uniform float u_time,u_pulse,u_aspect;
      uniform vec2 u_pointer;
      float noise(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      void main(){
        vec2 p=(v_uv-.5)*vec2(u_aspect,1.);
        float r=length(p),angle=atan(p.y,p.x);
        float mist=exp(-r*r*3.5);
        float folds=sin(angle*3.+r*10.-u_time*.11)*.5+.5;
        float ribbon=exp(-pow(p.y+.12*sin(p.x*5.+u_time*.08),2.)*30.)*.13;
        vec3 c=vec3(.022,.035,.055);
        c+=vec3(.015,.085,.077)*mist*(.4+folds*.6);
        c+=vec3(.095,.035,.082)*exp(-length(p-vec2(.37,.14))*3.5)*folds*.55;
        c+=vec3(.04,.12,.13)*ribbon;
        vec2 tap=(u_pointer-.5)*vec2(u_aspect,1.);
        float age=max(0.,u_time-u_pulse);
        float wave=exp(-pow(length(p-tap)-age*.18,2.)*1600.)*exp(-age*.75);
        c+=vec3(.11,.27,.25)*wave;
        c+=(noise(gl_FragCoord.xy)-.5)*.013;
        gl_FragColor=vec4(c,1.);
      }
    `);
    this.points=this.program(`
      precision highp float;
      attribute vec3 a_position,a_anchor,a_color;
      attribute float a_kind,a_index,a_random;
      uniform mat4 u_matrix;
      uniform float u_time,u_pulse,u_selected,u_dpr;
      varying vec3 v_color;
      varying float v_alpha;
      mat2 turn(float angle){return mat2(cos(angle),-sin(angle),sin(angle),cos(angle));}
      void main(){
        vec3 p=a_position;
        float energy=exp(-max(0.,u_time-u_pulse)*1.1);
        if(a_kind<.5){
          p.xz=turn(u_time*.085)*p.xz;
          p.yz=turn(.22+sin(u_time*.13)*.11)*p.yz;
          p*=1.+.045*sin(u_time*.8+a_random*6.28)+energy*.1*sin(length(p)*5.-u_time*4.);
        }else if(a_kind<1.5){
          p.xz=turn(u_time*.16+a_index)*p.xz;
          p.yz=turn(u_time*.09)*p.yz;
          p*=1.+energy*.35;
          p+=a_anchor;
          p.y+=sin(u_time*.6+a_index)*.09;
        }else if(a_kind>2.5){p.xz=turn(-u_time*.028)*p.xz;}
        vec4 clip=u_matrix*vec4(p,1.);
        gl_Position=clip;
        float focus=(abs(a_index-u_selected)<.1&&a_kind>.5&&a_kind<1.5)?1.:0.;
        float size=a_kind>1.5&&a_kind<2.5?2.1:4.4;
        gl_PointSize=clamp(size*u_dpr*6./max(1.,clip.w),1.,12.*u_dpr)*(1.+focus*.35);
        v_color=a_color*(1.+focus*.4);
        v_alpha=a_kind>1.5&&a_kind<2.5?.45:(a_kind>2.5?.22:.62);
        v_alpha*=.8+.2*sin(u_time*.6+a_random*30.);
      }
    `, `
      precision mediump float;
      varying vec3 v_color;
      varying float v_alpha;
      void main(){
        float d=length(gl_PointCoord-.5)*2.;
        float halo=exp(-d*d*3.8),core=exp(-d*d*35.);
        gl_FragColor=vec4(v_color*(halo*.7+core*.5),v_alpha*(1.-smoothstep(.5,1.,d)));
      }
    `);
    this.quad=gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER,this.quad);
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array([-1,-1,1,-1,-1,1,-1,1,1,-1,1,1]),gl.STATIC_DRAW);
    this.buffer=gl.createBuffer();
    const uniforms=(program,names)=>Object.fromEntries(names.map(name=>[name,gl.getUniformLocation(program,'u_'+name)]));
    this.bgUniforms=uniforms(this.background,['time','pulse','aspect','pointer']);
    this.pointUniforms=uniforms(this.points,['matrix','time','pulse','selected','dpr']);
    this.pointAttributes=['position','anchor','color','kind','index','random'].map(name=>gl.getAttribLocation(this.points,'a_'+name));
  }

  setQuests(quests) {
    this.anchors=quests.map((quest,index)=>({id:quest.id,index,position:index===0?[-2.55,-.16,.45]:index===1?[2.55,-.55,-.55]:[Math.cos(index*2.4)*3,Math.sin(index*2.4)*1.2,0]}));
    if(!this.gl) return;
    const vertices=[];
    let randomState=314159;
    const random=()=>{randomState=(Math.imul(randomState,1664525)+1013904223)>>>0;return randomState/4294967296;};
    const add=(position,anchor,color,kind,index=-1)=>vertices.push(...position,...anchor,...color,kind,index,random());
    // A torus knot woven from fine filaments rather than an opaque mesh.
    for(let uIndex=0;uIndex<430;uIndex++) {
      const u=uIndex/430*Math.PI*2;
      const center=[(1.15+.43*Math.cos(3*u))*Math.cos(2*u),(1.15+.43*Math.cos(3*u))*Math.sin(2*u),.58*Math.sin(3*u)];
      for(let vIndex=0;vIndex<56;vIndex++) {
        const v=vIndex/56*Math.PI*2,tube=.17+.04*Math.sin(u*12),jitter=(random()-.5)*.016;
        const p=[center[0]+Math.cos(v)*Math.cos(2*u)*tube,center[1]+Math.cos(v)*Math.sin(2*u)*tube,center[2]+Math.sin(v)*tube+jitter];
        const warm=Math.pow(.5+.5*Math.sin(u*3+v*.7),5);
        add(p,[0,0,0],[.21+warm*.58,.68-warm*.13,.72-warm*.39],0);
      }
    }
    for(const seed of this.anchors) {
      const color=seed.index%2===0?[1,.68,.31]:[.7,.65,1];
      for(let i=0;i<1700;i++) {
        const y=1-2*(i+.5)/1700,radius=Math.sqrt(1-y*y),angle=i*2.399963,petal=1+.1*Math.sin(angle*5+y*9);
        add([Math.cos(angle)*radius*.24*petal,y*.34,Math.sin(angle)*radius*.24*petal],seed.position,color,1,seed.index);
      }
    }
    for(let i=0;i<2100;i++) {
      const p=[(random()-.5)*25,(random()-.5)*16,(random()-.5)*18-3],tint=random();
      add(p,[0,0,0],[.4+tint*.3,.65+tint*.2,.7+tint*.25],2);
    }
    for(let i=0;i<1900;i++) {
      const a=i/1900*Math.PI*2;
      add([Math.cos(a)*3.2,Math.sin(a)*.2-.12,Math.sin(a)*2.3],[0,0,0],[.18,.47,.5],3);
    }
    this.count=vertices.length/12;
    const gl=this.gl;
    gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);
    gl.bufferData(gl.ARRAY_BUFFER,new Float32Array(vertices),gl.STATIC_DRAW);
    this.resize();
  }

  resize() {
    this.width=this.canvas.clientWidth;
    this.height=this.canvas.clientHeight;
    this.dpr=Math.min(devicePixelRatio||1,this.width<600?1.25:1.5);
    this.canvas.width=Math.round(this.width*this.dpr);
    this.canvas.height=Math.round(this.height*this.dpr);
    if(this.gl) this.gl.viewport(0,0,this.canvas.width,this.canvas.height);
    else if(this.anchors.length) this.onProject(this.anchors.map(anchor=>({id:anchor.id,index:anchor.index,x:this.width*(anchor.index%2?.76:.26),y:this.height*.55})),{width:this.width,height:this.height});
    this.requestFrame();
  }

  bindInput() {
    this.canvas.addEventListener('pointerdown',event=>{
      this.pointers.set(event.pointerId,[event.clientX,event.clientY]);
      this.canvas.setPointerCapture(event.pointerId);
      this.start=[event.clientX,event.clientY];this.moved=false;this.pinch=this.pinchDistance();
    });
    this.canvas.addEventListener('pointermove',event=>{
      this.pointer=[event.clientX/innerWidth,1-event.clientY/innerHeight];
      if(this.pointers.has(event.pointerId)) {
        const previous=this.pointers.get(event.pointerId);
        this.pointers.set(event.pointerId,[event.clientX,event.clientY]);
        if(this.pointers.size>1) {
          const next=this.pinchDistance();
          if(this.pinch&&next) this.distance=Math.max(6.7,Math.min(12,this.distance*this.pinch/next));
          this.pinch=next;
        }else {
          this.yaw+=(event.clientX-previous[0])*.004;
          this.pitch=Math.max(-.5,Math.min(.55,this.pitch+(event.clientY-previous[1])*.003));
        }
        if(Math.hypot(event.clientX-this.start[0],event.clientY-this.start[1])>6) this.moved=true;
        this.requestFrame();
      }
    });
    const release=event=>{
      const hadPointer=this.pointers.has(event.pointerId);this.pointers.delete(event.pointerId);
      if(hadPointer&&!this.moved&&event.type==='pointerup') this.stir();
    };
    this.canvas.addEventListener('pointerup',release);
    this.canvas.addEventListener('pointercancel',release);
    this.canvas.addEventListener('wheel',event=>{
      if(!this.active) return;
      event.preventDefault();this.distance=Math.max(6.7,Math.min(12,this.distance+event.deltaY*.006));this.requestFrame();
    },{passive:false});
    this.canvas.addEventListener('webglcontextlost',event=>{
      event.preventDefault();this.gl=null;document.documentElement.dataset.renderer='fallback';this.requestFrame();
    });
  }

  pinchDistance() {
    const points=[...this.pointers.values()];
    return points.length<2?0:Math.hypot(points[0][0]-points[1][0],points[0][1]-points[1][1]);
  }

  stir() {
    this.pulse=this.time;
    if(this.paused)this.time+=.15;
    if(!this.gl) {
      const art=document.querySelector('.fallback-art');
      if(this.paused)art.style.filter='brightness(1.6)';
      else art.animate([{filter:'brightness(1)'},{filter:'brightness(2.5)'},{filter:'brightness(1)'}],{duration:900});
    }
    this.tone(0);this.requestFrame();
  }
  select(index) {this.selected=index;this.pulse=this.time;this.tone(index);this.requestFrame();}

  async setSound(enabled) {
    if(enabled) {
      const AudioContext=window.AudioContext||window.webkitAudioContext;
      if(!AudioContext)return false;
      try {this.audio??=new AudioContext();await this.audio.resume();this.sound=true;this.tone(0);}
      catch {this.sound=false;}
    }else {this.sound=false;if(this.audio)await this.audio.suspend();}
    return this.sound;
  }

  tone(index) {
    if(!this.sound||!this.audio)return;
    if(this.audio.state==='suspended') {
      this.audio.resume().then(()=>{if(this.sound)this.tone(index);}).catch(()=>{});
      return;
    }
    if(this.audio.state!=='running')return;
    const now=this.audio.currentTime;
    if(this.lastTone&&now-this.lastTone<.24)return;
    this.lastTone=now;
    const base=index%2?146.83:110;
    for(const ratio of [1,1.5,2,2.5]) {
      const oscillator=this.audio.createOscillator(),envelope=this.audio.createGain();
      oscillator.type='sine';oscillator.frequency.value=base*ratio;
      envelope.gain.setValueAtTime(0,now);envelope.gain.linearRampToValueAtTime(.025/ratio,now+.08);
      envelope.gain.exponentialRampToValueAtTime(.0001,now+1.8);
      oscillator.connect(envelope);envelope.connect(this.audio.destination);
      oscillator.start(now);oscillator.stop(now+1.9);
      oscillator.onended=()=>{oscillator.disconnect();envelope.disconnect();};
    }
  }

  setActive(active) {this.active=active;this.requestFrame();}
  setPaused(paused) {this.paused=paused;this.requestFrame();}
  requestFrame() {
    if(this.frameId!==null)cancelAnimationFrame(this.frameId);
    this.frameId=null;
    if(document.hidden||!this.active)return;
    this.frameId=requestAnimationFrame(t=>this.frame(t));
  }

  frame(timestamp) {
    this.frameId=null;
    if(document.hidden||!this.active)return;
    if(!this.gl) {
      document.querySelector('.fallback-art svg').style.transform=`rotate(${this.yaw*.3}rad) scale(${8.8/this.distance})`;
      return;
    }
    if(!this.count)return;
    const step=this.lastFrame?Math.min((timestamp-this.lastFrame)/1000,.04):0;
    this.lastFrame=timestamp;if(!this.paused)this.time+=step;
    this.draw();
    if(!this.paused)this.frameId=requestAnimationFrame(t=>this.frame(t));
  }

  matrix() {
    const aspect=this.width/this.height,distance=this.width<600?this.distance+2.8:this.distance;
    const yaw=this.yaw+(this.paused?0:Math.sin(this.time*.09)*.055);
    const eye=[Math.sin(yaw)*Math.cos(this.pitch)*distance,Math.sin(this.pitch)*distance,Math.cos(yaw)*Math.cos(this.pitch)*distance];
    const norm=v=>{const d=Math.hypot(...v);return v.map(x=>x/d);};
    const cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];
    const dot=(a,b)=>a.reduce((sum,v,i)=>sum+v*b[i],0);
    const z=norm(eye),x=norm(cross([0,1,0],z)),y=cross(z,x);
    const view=[x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1];
    const f=1/Math.tan((this.width<600?.98:.62)/2),near=.1,far=60;
    const projection=[f/aspect,0,0,0,0,f,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0];
    const matrix=new Float32Array(16);
    for(let col=0;col<4;col++)for(let row=0;row<4;row++)for(let k=0;k<4;k++)matrix[col*4+row]+=projection[k*4+row]*view[col*4+k];
    return matrix;
  }

  draw() {
    const gl=this.gl,matrix=this.matrix();
    gl.disable(gl.BLEND);gl.useProgram(this.background);gl.bindBuffer(gl.ARRAY_BUFFER,this.quad);
    const position=gl.getAttribLocation(this.background,'a_position');
    gl.enableVertexAttribArray(position);gl.vertexAttribPointer(position,2,gl.FLOAT,false,0,0);
    const bg=this.bgUniforms;
    gl.uniform1f(bg.time,this.time);gl.uniform1f(bg.pulse,this.pulse);gl.uniform1f(bg.aspect,this.width/this.height);gl.uniform2fv(bg.pointer,this.pointer);
    gl.drawArrays(gl.TRIANGLES,0,6);gl.disableVertexAttribArray(position);
    gl.useProgram(this.points);gl.bindBuffer(gl.ARRAY_BUFFER,this.buffer);
    const sizes=[3,3,3,1,1,1];let offset=0;
    this.pointAttributes.forEach((attribute,index)=>{
      if(attribute>=0){gl.enableVertexAttribArray(attribute);gl.vertexAttribPointer(attribute,sizes[index],gl.FLOAT,false,48,offset*4);}offset+=sizes[index];
    });
    gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE);
    const uniforms=this.pointUniforms;
    gl.uniformMatrix4fv(uniforms.matrix,false,matrix);gl.uniform1f(uniforms.time,this.time);gl.uniform1f(uniforms.pulse,this.pulse);gl.uniform1f(uniforms.selected,this.selected);gl.uniform1f(uniforms.dpr,this.dpr);
    gl.drawArrays(gl.POINTS,0,this.count);
    this.pointAttributes.forEach(attribute=>{if(attribute>=0)gl.disableVertexAttribArray(attribute);});
    const pins=this.anchors.map(anchor=>{
      const p=[...anchor.position,1];p[1]+=Math.sin(this.time*.6+anchor.index)*.09;
      const clip=[0,0,0,0];for(let row=0;row<4;row++)for(let k=0;k<4;k++)clip[row]+=matrix[k*4+row]*p[k];
      return {id:anchor.id,index:anchor.index,x:(clip[0]/clip[3]*.5+.5)*this.width,y:(.5-clip[1]/clip[3]*.5)*this.height};
    });
    this.onProject(pins,{width:this.width,height:this.height});
  }
};
