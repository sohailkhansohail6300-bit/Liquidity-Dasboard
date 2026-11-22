// Runs the ORIGINAL prototype code (data.js + the exact functions from app.js / market.html / trades.html /
// comparison.html) in Node and prints every derived number as JSON, for comparison with backend/market/sim.py.
const fs = require('fs'), vm = require('vm');
const SRC = process.argv[2];
const sandbox = { window: {}, localStorage: { getItem() { return null; }, setItem() {}, removeItem() {} }, document: { addEventListener() {}, getElementById() { return null; }, readyState: 'complete', querySelectorAll() { return []; } }, location: { href: 'http://x/', search: '' }, Intl, URLSearchParams, URL, console, Date, Math, JSON };
sandbox.window = sandbox; sandbox.navigator = {};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(SRC + '/js/data.js', 'utf8'), sandbox);
vm.runInContext(fs.readFileSync(SRC + '/js/app.js', 'utf8'), sandbox);
const App = sandbox.App, D = App.D;
// market.html model() & split(), copied verbatim
const N = 364;
function split(r,n,total,lo,hi,wts){var w=[],sum=0,i;for(i=0;i<n;i++){w.push((wts?wts[i]:1)*(lo+r()*(hi-lo)));sum+=w[i];}var out=[],acc=0;for(i=0;i<n;i++){out.push(Math.floor(total*w[i]/sum));acc+=out[i];}var rem=total-acc;i=0;while(rem>0){out[i%n]++;rem--;i++;}return out;}
function model(co){
 var K=D.KPI[co.id],sub=App.subs()[co.id],r=App.rng(App.seedOf(co.id)+4242),price=App.series(co.id,N,5),tot=new Array(N),del=new Array(N),i;
 var daysSince=sub&&sub.startIso?Math.round((Date.parse(D.TODAY)-Date.parse(sub.startIso))/86400000):N;
 var s0=Math.max(0,N-1-daysSince);
 var d24=Math.round(K['24h'].vol*K['24h'].share/100),d7=Math.round(K['7d'].vol*K['7d'].share/100),d30=Math.round(K['30d'].vol*K['30d'].share/100),dS=Math.round(K.since.vol*K.since.share/100);
 var segs=[[N-1,N-1,K['24h'].vol,d24],[N-7,N-2,K['7d'].vol-K['24h'].vol,d7-d24],[N-30,N-8,K['30d'].vol-K['7d'].vol,d30-d7]];
 if(s0<N-30)segs.push([s0,N-31,K.since.vol-K['30d'].vol,dS-d30]);
 segs.forEach(function(g){var n=g[1]-g[0]+1,t=split(r,n,g[2],0.6,1.4),dl=split(r,n,g[3],0.8,1.2,t);for(var k=0;k<n;k++){tot[g[0]+k]=t[k];del[g[0]+k]=dl[k];}});
 var avg=co.vol30/30;for(i=0;i<(s0<N-30?s0:N-30);i++){tot[i]=Math.round(avg*(0.5+r()*1.0));del[i]=0;}
 var days=[];for(i=0;i<N;i++)days.push({iso:App.addIso(D.TODAY,i-(N-1)),p:price[i].p,tot:tot[i],del:del[i]});
 return {days:days,d24:d24,d30:d30,dS:dS};
}
var VENUES={XETRA:['XETRA','Tradegate','XETRA'],Euronext:['Euronext Amsterdam','Cboe Europe','Euronext Amsterdam']};
function trades(co){
 var r=App.rng(App.seedOf(co.id)+99),out=[],day=23,min=14*60+22,no=88241;
 for(var i=0;i<30;i++){
  var side=r()<0.52?'Buy':'Sell',sh=Math.round((500+r()*r()*24000)/100)*100,pr=co.price*(0.985+r()*0.03),v=VENUES[co.exch];
  out.push({iso:'2026-10-'+String(day).padStart(2,'0'),dt:day+' Oct 2026 · '+String(Math.floor(min/60)).padStart(2,'0')+':'+String(min%60).padStart(2,'0'),id:co.code+'-'+(no-=Math.round(8+r()*60)),side:side,sh:sh,pr:pr,val:sh*pr,venue:v[Math.floor(r()*v.length)]});
  min-=Math.round(60+r()*240);if(min<9*60){min=17*60+Math.round(r()*25);day-=(day%7===6?3:1);if(day<1)day=1;}
 }
 return out;
}
var PER={'3m':{f:[0.97,1.04,0.99,0.96]},'6m':{f:[0.93,1.08,0.98,0.92]},'1y':{f:[0.88,1.13,0.97,0.88]}},KEYS=['vol','spr','tim','turn'];
function pdata(id,g,per){
 var k=D.KPI[id]['30d'],f=PER[per].f,r=App.rng(App.seedOf(id)+per.charCodeAt(0)*7+per.length),out=[];
 App.MEASURES.forEach(function(m,i){
  var drift=1+(f[i]-1)*0.8+(r()-0.5)*0.06,v=k[KEYS[i]]*drift;if(i===2)v=Math.min(99.9,v);
  out.push({v:v,lo:g.lo[i]*f[i],hi:g.hi[i]*f[i],med:g.median[i]*f[i]});
 });
 return out;
}
const out = {};
D.ORDER.forEach(id => {
  const co = D.COMPANIES[id];
  out[id] = { series30: App.series(id, 30), series12: App.series(id, 12), series7: App.series(id, 7), model: model(co), trades: trades(co),
    peers: D.PEER_GROUPS.map(g => ({ id: g.id, '3m': pdata(id, g, '3m'), '6m': pdata(id, g, '6m'), '1y': pdata(id, g, '1y'), position: App.position(id, g) })) };
});
// access log stamps
function stampOf(i){var d=new Date(Date.UTC(2026,9,22,8,41)-i*7*60000);return {text:new Intl.DateTimeFormat('en-GB',{weekday:'short',day:'2-digit',month:'short',year:'numeric',hour:'2-digit',minute:'2-digit',hour12:true,timeZone:'UTC'}).format(d).replace(',',''),iso:d.toISOString().slice(0,16).replace('T',' ')};}
out.stamps = Array.from({length: 1096}, (_, i) => stampOf(i));
process.stdout.write(JSON.stringify(out));
