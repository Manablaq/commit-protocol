# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from datetime import datetime,timezone
import json
from genlayer import *
from genlayer.py.keccak import Keccak256
E=gl.vm.UserError
PROTOCOL="commit";REVISION="0.7.0-reviewable-manifest";P="983307fac383ac4a92be6c0c361ea8f3c9d9efa20ad5e6e8bc8dee932f2a6103";R="all-evidence-and-effects-v1";S="commit-evidence-v2";D="commit-decision-v3";Q="commit-mission-receipt-v2";N="commit-mission-manifest-v2";U=(1<<256)-1
K=('DECISION_PENDING','invalid authority host','invalid authority path prefix','authority version','PREPARING','record version','mission version','REPAIR_REQUIRED','active_evidence_root','mission is not preparing','preparation deadline has passed','supplier is not authorized','mission is not sealed','mission already evaluated','recovery deadline has passed','dependency effect not found','SEALED','mission is underfunded','evidence failure not found','repair authority version mismatch','repair record identity mismatch','invalid mission id','owner required')
@gl.evm.contract_interface
class _NativeRecipient:
 class View:pass
 class Write:pass
class CommitProtocol(gl.Contract):
 o:Address;n:u256;w:u256;d:TreeMap[str,str];hh:Address
 def __init__(self,helper:Address):self.o=gl.message.sender_address;self.n=0;self.w=0;self.hh=helper
 def q(self):return gl.get_contract_at(self.hh).view()
 def j(self,k):
  x=self.d.get(k,"")
  if not x:raise E("withdrawal not found")
  return json.loads(x)
 def J(self,k,x):self.d[k]=json.dumps(x,ensure_ascii=True,sort_keys=True,separators=(",",":"))
 def g(self,x):return json.dumps(x,separators=(",",":"))
 def m(self,i):
  x=self.d.get("m:"+i,"")
  if not x:raise E("mission not found")
  return json.loads(x)
 def M(self,i,x):self.J("m:"+i,x)
 def a(self,i):
  x=self.d.get("a:"+i,"")
  if not x:raise E("authority not found")
  return json.loads(x)
 def A(self,h):return Address(bytes.fromhex(h[2:]))
 def t(self):return int(datetime.now(timezone.utc).timestamp())
 def u(self,v,l,p=False):
  if type(v)is not int or v<(1 if p else 0)or v>U:raise E("invalid "+l)
  return v
 def x(self,v,l):
  if len(v)!=64 or any(c not in"0123456789abcdef"for c in v):raise E(l+" must be 32-byte lowercase hex")
 def z(self,v,l,n=512):
  if not v or len(v)>n or any(ord(c)<32 or ord(c)>126 for c in v):raise E("invalid "+l)
 def k(self,v,l,n=512):
  self.z(v,l,n)
  if any(c not in"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"for c in v):raise E("invalid "+l)
 def Z(self,v,l):
  if v.as_hex=="0x"+"00"*20:raise E(l+" cannot be zero")
 def f(self,v):return str(len(v))+":"+v
 def p(self,i):
  m=self.m(i)
  if gl.message.sender_address.as_hex!=m[0]:raise E("principal required")
  return m
 def e(self,m,i):
  for e in m[25]:
   if e[0]==i:return e
  raise E("evidence not found")
 def F(self,m,i):
  for f in m[24]:
   if f[0]==i:return f
  raise E("effect not found")
 def T(self,a,r,v):
  x=self.d.get("t:"+a+":"+r+":"+str(v),"")
  if not x:raise E("evidence attestation not found")
  return json.loads(x)
 def b(self,i,r):
  m=self.m(i)
  if m[14]:return
  m[15]="ABORT";m[16]=r;m[11]=m[8];m[14]=True;m[1]="ABORTED";m[26][m[10]]=int(m[26].get(m[10],0))+m[8];self.M(i,m);k="c:"+m[10];self.d[k]=str(int(self.d.get(k,"0"))+m[8])
 def c(self,i):
  m=self.m(i)
  if m[8]<m[9]:raise E(K[17])
  for f in m[24]:
   a=f[4];v=f[5];m[26][a]=int(m[26].get(a,0))+v;k="c:"+a;self.d[k]=str(int(self.d.get(k,"0"))+v)
  q=m[8]-m[9];m[11]=q;m[26][m[10]]=int(m[26].get(m[10],0))+q;k="c:"+m[10];self.d[k]=str(int(self.d.get(k,"0"))+q);m[14]=True;m[1]="COMMITTED";self.M(i,m)
 @gl.public.write
 def register_authority(self,authority_id:str,host:str,path_prefix:str,issuer_address:Address,authority_version:int)->None:
  if gl.message.sender_address!=self.o:raise E(K[22])
  self.k(authority_id,"authority id",64)
  if self.d.get("a:"+authority_id,""):raise E("authority already exists")
  self.z(host,K[1],253)
  if host!=host.lower()or any(c in host for c in"/?:#@%\\")or host.startswith(".")or host.endswith(".")or".."in host:raise E(K[1])
  for q in host.split("."):
   if not 1<=len(q)<=63 or q[0]=="-"or q[-1]=="-"or any(c not in"abcdefghijklmnopqrstuvwxyz0123456789-"for c in q):raise E(K[1])
  self.z(path_prefix,K[2])
  if not path_prefix.startswith("/")or"//"in path_prefix or any(c in path_prefix for c in("?", "#","%","\\"))or(path_prefix!="/"and path_prefix.endswith("/"))or any(c in(".","..")for c in path_prefix.split("/")):raise E(K[2])
  self.Z(issuer_address,"issuer");self.u(authority_version,K[3],True);self.J("a:"+authority_id,[True,host,path_prefix,issuer_address.as_hex,authority_version])
 @gl.public.write
 def deactivate_authority(self,authority_id:str)->None:
  if gl.message.sender_address!=self.o:raise E(K[22])
  a=self.a(authority_id);a[0]=False;self.J("a:"+authority_id,a)
 @gl.public.write
 def authorize_supplier(self,mission_id:str,supplier:Address)->None:
  m=self.p(mission_id)
  if m[1]!=K[4]:raise E(K[9])
  if self.t()>m[18]:raise E(K[10])
  self.Z(supplier,"supplier");h=supplier.as_hex
  if m[22].get(h,False):raise E("supplier already authorized")
  m[22][h]=True;m[23]+=1;self.M(mission_id,m)
 @gl.public.write
 def revoke_supplier(self,mission_id:str,supplier:Address)->None:
  m=self.p(mission_id)
  if m[1]!=K[4]:raise E(K[9])
  h=supplier.as_hex
  if h==m[0]:raise E("principal cannot be revoked")
  if not m[22].get(h,False):raise E(K[11])
  if any(f[1]==h for f in m[24]):raise E("supplier has a prepared effect")
  m[22][h]=False;m[23]=max(0,m[23]-1);self.M(mission_id,m)
 @gl.public.write
 def attest_evidence(self,authority_id:str,authority_version:int,record_id:str,record_version:int,mission_id:str,mission_version:int,url:str,record_hash:str,published_at:int,expires_at:int)->None:
  a=self.a(authority_id)
  if not a[0]:raise E("authority is inactive")
  self.u(authority_version,K[3],True)
  if authority_version!=a[4]:raise E("authority version mismatch")
  if gl.message.sender_address.as_hex!=a[3]:raise E("issuer required")
  self.k(record_id,"record id");self.u(record_version,K[5],True);m=self.m(mission_id);self.u(mission_version,K[6],True)
  if mission_version!=m[21]:raise E(K[6])
  if not self.q().url_ok(url,a[1],a[2]):raise E("evidence URL is outside authority")
  self.x(record_hash,"record hash");self.u(published_at,"published",True);self.u(expires_at,"expiry",True)
  if published_at<m[20]:raise E("evidence published before mission")
  if expires_at<m[19]:raise E("invalid evidence expiry")
  k="t:"+authority_id+":"+record_id+":"+str(record_version)
  if self.d.get(k,""):raise E("attestation already exists")
  self.J(k,[authority_id,authority_version,a[3],record_id,record_version,mission_id,mission_version,url,record_hash,published_at,expires_at])
 @gl.public.write
 def register_evidence(self,mission_id:str,evidence_id:str,authority_id:str,authority_version:int,record_id:str,record_version:int)->None:
  m=self.p(mission_id)
  if m[1]!=K[4]:raise E(K[9])
  if self.t()>m[18]:raise E(K[10])
  self.k(evidence_id,"evidence id")
  if any(e[0]==evidence_id for e in m[25]):raise E("evidence already exists")
  if len(m[25])>=16:raise E("evidence limit exceeded")
  self.a(authority_id);self.u(authority_version,K[3],True);self.k(record_id,"record id");self.u(record_version,K[5],True);t=self.T(authority_id,record_id,record_version)
  if t[1]!=authority_version:raise E("authority version mismatch")
  if t[5]!=mission_id:raise E("attestation mission mismatch")
  if t[6]!=m[21]:raise E("attestation mission version mismatch")
  m[25].append([evidence_id,authority_id,authority_version,t[2],record_id,record_version,mission_id,m[21],t[7],t[8],mission_id,t[9],t[10],None,None]);self.M(mission_id,m)
 @gl.public.write
 def create_mission(self,mission_id:str,objective:str,policy_digest:str,budget:int,refund_beneficiary:Address,prepare_deadline:int,recovery_deadline:int)->None:
  self.z(mission_id,"mission id")
  if":"in mission_id:raise E(K[21])
  self.z(objective,"objective");self.x(policy_digest,"policy digest");self.u(budget,"mission budget",True);self.u(prepare_deadline,"preparation deadline",True);self.u(recovery_deadline,"recovery deadline",True)
  if policy_digest!=P:raise E("unsupported policy rule")
  if self.d.get("m:"+mission_id,""):raise E("mission already exists")
  self.Z(refund_beneficiary,"refund beneficiary")
  if recovery_deadline<=prepare_deadline:raise E("invalid deadline order")
  h=gl.message.sender_address.as_hex;m=[h,K[4],objective,policy_digest,"","","",budget,0,0,refund_beneficiary.as_hex,0,"","",False,"","",0,prepare_deadline,recovery_deadline,self.t(),1,{h:True},1,[],[],{}];m[4]=self.q().intent(self.g([int(gl.message.chain_id),gl.message.contract_address.as_hex,mission_id,m[2],m[3],m[7],m[10],m[18],m[19]]));self.M(mission_id,m);self.d["i:"+str(int(self.n))]=mission_id;self.n=int(self.n)+1
 @gl.public.write.payable
 def fund_mission(self,mission_id:str)->None:
  m=self.p(mission_id)
  if m[1]!=K[4]:raise E(K[9])
  if self.t()>m[18]:raise E(K[10])
  a=int(gl.message.value)
  if a<=0:raise E("funding value must be positive")
  if m[8]+a>m[7]:raise E("funding exceeds mission budget")
  m[8]+=a;self.M(mission_id,m)
 @gl.public.write
 def prepare_effect(self,mission_id:str,effect_id:str,effect_digest:str,beneficiary:Address,value:int,expiry:int)->None:self._p(mission_id,effect_id,effect_digest,beneficiary,value,expiry,"")
 @gl.public.write
 def prepare_effect_with_dependency(self,mission_id:str,effect_id:str,effect_digest:str,beneficiary:Address,value:int,expiry:int,dependency_id:str)->None:self._p(mission_id,effect_id,effect_digest,beneficiary,value,expiry,dependency_id)
 def _p(self,i,e,d,b,v,x,p):
  m=self.m(i)
  if m[1]!=K[4]:raise E(K[9])
  if self.t()>m[18]:raise E(K[10])
  self.u(v,"effect value",True);self.u(x,"effect expiry",True);s=gl.message.sender_address.as_hex
  if not m[22].get(s,False):raise E(K[11])
  if not e or len(e)>512 or":"in e:raise E("invalid effect id")
  self.z(e,"effect id")
  if any(q[0]==e for q in m[24]):raise E("effect already exists")
  if len(m[24])>=32:raise E("effect limit exceeded")
  self.x(d,"effect digest")
  if p:
   self.k(p,"dependency id")
   if p==e:raise E("effect cannot depend on itself")
   try:self.F(m,p)
   except:raise E(K[15])
  self.Z(b,"effect beneficiary")
  if m[9]+v>m[7]:raise E("prepared effects exceed mission budget")
  if x<m[19]:raise E("invalid effect expiry")
  m[24].append([e,s,d,p,b.as_hex,v,x]);m[9]+=v;self.M(i,m)
 @gl.public.write
 def seal_mission(self,mission_id:str,effect_root:str,evidence_root:str)->None:
  m=self.p(mission_id)
  if m[1]!=K[4]:raise E(K[9])
  if self.t()>m[18]:raise E(K[10])
  if not m[24]:raise E("mission has no prepared effects")
  if len(m[25])<2:raise E("mission needs two evidence records")
  if m[8]<m[9]:raise E(K[17])
  if len({e[3]for e in m[25]})<2:raise E("evidence authorities must be distinct")
  for f in m[24]:
   n=0;p=f[3]
   while p:
    try:p=self.F(m,p)[3]
    except:raise E(K[15])
    n+=1
    if n>=len(m[24]):raise E("effect graph contains a cycle")
  self.x(effect_root,"effect root");self.x(evidence_root,"evidence root")
  if effect_root!=self.derive_effect_root(mission_id):raise E("effect root does not match prepared effects")
  if evidence_root!=self.derive_evidence_root(mission_id):raise E("evidence root does not match registered evidence")
  m[5]=effect_root;m[6]=evidence_root;m[1]=K[16];self.M(mission_id,m)
 @gl.public.write
 def cancel_mission(self,mission_id:str)->None:
  m=self.p(mission_id)
  if m[1]!=K[4]:raise E("sealed mission cannot be cancelled")
  self.b(mission_id,"cancelled_by_principal")
 @gl.public.write
 def repair_evidence(self,mission_id:str,evidence_id:str,authority_id:str,authority_version:int,record_id:str,record_version:int)->None:
  m=self.p(mission_id)
  if m[1]!=K[16]:raise E(K[12])
  if m[15]:raise E(K[13])
  if self.t()>=m[19]:raise E(K[14])
  e=self.e(m,evidence_id);f=e[13]
  if not f:raise E(K[18])
  if authority_id!=e[1]:raise E("repair authority mismatch")
  if authority_version!=e[2]:raise E(K[19])
  if record_id!=e[4]:raise E(K[20])
  self.u(record_version,K[5],True);c=e[14][6]if e[14]else e[5]
  if record_version<=c:raise E("repair record version must be newer")
  try:t=self.T(authority_id,record_id,record_version)
  except:raise E("repair evidence attestation not found")
  if t[1]!=authority_version:raise E(K[19])
  if t[5]!=mission_id:raise E("repair attestation mission mismatch")
  if t[6]!=m[21]:raise E("repair attestation mission version mismatch")
  if t[3]!=e[4]:raise E(K[20])
  if t[2]!=e[3]:raise E("repair issuer mismatch")
  e[14]=["READY",authority_id,authority_version,t[2],record_id,e[5],record_version,t[7],t[8],t[9],t[10]];self.M(mission_id,m)
 @gl.public.write
 def evaluate_mission(self,mission_id:str)->None:
  m=self.m(mission_id)
  if m[1]!=K[16]:raise E(K[12])
  if m[15]:raise E(K[13])
  if self.t()>=m[19]:raise E(K[14])
  ss=[]
  for e in m[25]:
   x=e[14];ss.append([e[0],x[1]if x else e[1],x[7]if x else e[8],x[8]if x else e[9],x[10]if x else e[12],x[4]if x else e[4],x[6]if x else e[5]])
  ids=[f[0]for f in m[24]];aer=self.q().evidence_root(self.g(m[25]),True);raw=[];r=None
  for i,e in enumerate(ss):
   def L():
    z=gl.nondet.web.get(e[2]);return[z.status,z.body.hex()if isinstance(z.body,bytes)else None]
   def V(x):
    if not isinstance(x,gl.vm.Return):return False
    try:return x.calldata==L()
    except:return False
   raw.append(gl.vm.run_nondet(L,V));meta=[mission_id,m[21],m[2],m[3],m[4],m[5],m[6],aer,ss[:i+1],ids];r=self.q().evaluate(self.g(meta),self.g(raw))
   if r.get("outcome")==K[7]:
    q=self.e(m,r["evidence_id"]);n=(q[13][6]if q[13]else 0)+1;q[13]=[K[7],r["failure_code"],r["evidence_id"],r["record_id"],r["record_version"],r["mission_version"],n];self.M(mission_id,m);return
  if r is None or r.get("outcome")!="DECISION":raise E("invalid consensus outcome")
  if r["decision"]not in("COMMIT","ABORT"):raise E("invalid consensus decision")
  m[15]=r["decision"];m[16]=r["reason_code"];m[17]+=1;m[13]=r[K[8]];z=D+self.f(mission_id)+self.f(str(m[21]))+self.f(r["decision"])+self.f(r["reason_code"])+self.f(m[5])+self.f(m[6])+self.f(r[K[8]]);m[12]=Keccak256(z.encode()).hexdigest();m[1]=K[0];self.M(mission_id,m);gl.get_contract_at(gl.message.contract_address).emit(on="finalized").apply_decision(mission_id,m[12])
 @gl.public.write
 def apply_decision(self,mission_id:str,decision_nonce:str)->None:
  if gl.message.sender_address!=gl.message.contract_address:raise E("self message required")
  m=self.m(mission_id)
  if m[14]:return
  if decision_nonce!=m[12]:raise E("decision nonce mismatch")
  if m[1]!=K[0]:raise E("decision is not pending")
  if m[15]=="COMMIT":self.c(mission_id)
  elif m[15]=="ABORT":self.b(mission_id,m[16])
  else:raise E("invalid decision")
 @gl.public.write
 def claim_mission(self,mission_id:str)->None:
  m=self.m(mission_id)
  if m[1]not in("COMMITTED","ABORTED"):raise E("mission is not allocated")
  b=gl.message.sender_address;h=b.as_hex;a=int(m[26].get(h,0))
  if a<=0:raise E("no claimable balance")
  i=str(int(self.w));m[26][h]=0;g=int(self.d.get("c:"+h,"0"))
  if g<a:raise E("claimable balance underflow")
  self.d["c:"+h]=str(g-a);self.M(mission_id,m);self.J("w:"+i,[mission_id,h,a,"DISPATCHED"]);self.w=int(self.w)+1;_NativeRecipient(b).emit_transfer(value=a)
 @gl.public.write
 def expire_mission(self,mission_id:str)->None:
  m=self.m(mission_id)
  if m[1]not in(K[4],K[16],K[0]):raise E("mission is already terminal")
  if self.t()<m[19]:raise E("recovery deadline has not passed")
  self.b(mission_id,"recovery_deadline_expired")
 @gl.public.view
 def protocol_info(self)->dict:return self.q().info(int(self.n))
 @gl.public.view
 def get_claimable(self,beneficiary:Address)->int:return int(self.d.get("c:"+beneficiary.as_hex,"0"))
 @gl.public.view
 def get_mission_claimable(self,mission_id:str,beneficiary:Address)->int:return int(self.m(mission_id)[26].get(beneficiary.as_hex,0))
 @gl.public.view
 def get_mission_receipt(self,mission_id:str)->dict:return self.q().fmt(1,self.g([mission_id,self.m(mission_id),int(gl.message.chain_id),gl.message.contract_address.as_hex]))
 @gl.public.view
 def get_withdrawal(self,withdrawal_id:str)->dict:return self.q().fmt(2,self.g([withdrawal_id,self.j("w:"+withdrawal_id)]))
 @gl.public.view
 def get_withdrawal_count(self)->int:return int(self.w)
 @gl.public.view
 def get_withdrawal_by_index(self,index:int)->dict:
  if index<0 or index>=int(self.w):raise E("withdrawal index out of range")
  return self.get_withdrawal(str(index))
 @gl.public.view
 def derive_intent_digest(self,mission_id:str)->str:
  m=self.m(mission_id);return self.q().intent(self.g([int(gl.message.chain_id),gl.message.contract_address.as_hex,mission_id,m[2],m[3],m[7],m[10],m[18],m[19]]))
 @gl.public.view
 def derive_effect_root(self,mission_id:str)->str:return self.q().effect_root(self.g(self.m(mission_id)[24]))
 @gl.public.view
 def derive_active_evidence_root(self,mission_id:str)->str:return self.q().evidence_root(self.g(self.m(mission_id)[25]),True)
 @gl.public.view
 def derive_evidence_root(self,mission_id:str)->str:return self.q().evidence_root(self.g(self.m(mission_id)[25]),False)
 @gl.public.view
 def get_evidence_failure(self,mission_id:str,evidence_id:str)->dict:
  f=self.e(self.m(mission_id),evidence_id)[13]
  if not f:raise E(K[18])
  return self.q().fmt(3,self.g(f))
 @gl.public.view
 def get_evidence_repair(self,mission_id:str,evidence_id:str)->dict:
  r=self.e(self.m(mission_id),evidence_id)[14]
  if not r:raise E("evidence repair not found")
  return self.q().fmt(4,self.g(r))
 @gl.public.view
 def get_mission(self,mission_id:str)->dict:return self.q().fmt(0,self.g([mission_id,self.m(mission_id)]))
 @gl.public.view
 def get_mission_by_index(self,index:int)->dict:
  if index<0 or index>=int(self.n):raise E("mission index out of range")
  return self.get_mission(self.d["i:"+str(index)])
 @gl.public.view
 def get_effect(self,mission_id:str,effect_id:str)->dict:return self.q().fmt(5,self.g([mission_id,self.F(self.m(mission_id),effect_id)]))
 @gl.public.view
 def get_effect_by_index(self,mission_id:str,index:int)->dict:
  m=self.m(mission_id)
  if index<0 or index>=len(m[24]):raise E("effect index out of range")
  return self.q().fmt(5,self.g([mission_id,m[24][index]]))
 @gl.public.view
 def get_authority(self,authority_id:str)->dict:return self.q().fmt(6,self.g([authority_id,self.a(authority_id)]))
 @gl.public.view
 def authorities_are_independent(self,authority_a:str,authority_b:str)->bool:return authority_a!=authority_b and self.a(authority_a)[3]!=self.a(authority_b)[3]
 @gl.public.view
 def get_evidence_attestation(self,authority_id:str,record_id:str,record_version:int)->dict:return self.q().fmt(7,self.g(self.T(authority_id,record_id,record_version)))
 @gl.public.view
 def get_evidence(self,mission_id:str,evidence_id:str)->dict:return self.q().fmt(8,self.g(self.e(self.m(mission_id),evidence_id)))
 @gl.public.view
 def get_evidence_by_index(self,mission_id:str,index:int)->dict:
  m=self.m(mission_id)
  if index<0 or index>=len(m[25]):raise E("evidence index out of range")
  return self.q().fmt(8,self.g(m[25][index]))
 @gl.public.view
 def get_mission_manifest(self,mission_id:str)->dict:
  m=self.m(mission_id);a=[]
  for e in m[25]:
   if not any(x[0]==e[1]for x in a):a.append([e[1],self.a(e[1])])
  return self.q().manifest(self.g([mission_id,m,int(gl.message.chain_id),gl.message.contract_address.as_hex,a]))
 @gl.public.view
 def is_supplier_authorized(self,mission_id:str,supplier:Address)->bool:return self.m(mission_id)[22].get(supplier.as_hex,False)
