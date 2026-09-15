# { "Depends": "py-genlayer:5jycge4q8k23462jtb0b9fyey1s9qz928sz2nbrd9mg4sxqg2qng" }
import json
import genlayer as gl
from genlayer import *
from genlayer.types.keccak import Keccak256
E=gl.vm.UserError
P="983307fac383ac4a92be6c0c361ea8f3c9d9efa20ad5e6e8bc8dee932f2a6103";R="all-evidence-and-effects-v1";S="commit-evidence-v2";V="0.7.0-reviewable-manifest"
class CommitHelper(gl.contract.Contract):
 def __init__(self):pass
 def f(self,v):return str(len(v))+":"+v
 def A(self,h):return Address(bytes.fromhex(h[2:]))
 @gl.public.view
 def url_ok(self,u:str,h:str,p:str)->bool:
  if not u or len(u)>2048 or any(ord(c)<32 or ord(c)>126 for c in u):return False
  x="https://"+h
  if not u.startswith(x):return False
  q=u[len(x):]
  if not q.startswith("/")or any(c in q for c in("?", "#","%","\\")):return False
  if q=="/":return p=="/"
  z=q.split("/")
  return not any(c in("",".","..")for c in z[1:])and(p=="/"or q==p or q.startswith(p+"/"))
 @gl.public.view
 def intent(self,data:str)->str:
  x=json.loads(data);q=("2","commit",V,str(x[0]),x[1],x[2],x[3],x[4],str(x[5]),x[6],str(x[7]),str(x[8]))
  return Keccak256(("commit-intent-v2"+"".join(self.f(v)for v in q)).encode()).hexdigest()
 def ef(self,f):
  q=(f[0],f[2],f[3],f[1],f[4],str(f[5]),str(f[6]))
  return Keccak256(("commit-effect-leaf-v1"+"".join(self.f(x)for x in q)).encode()).hexdigest()
 @gl.public.view
 def effect_root(self,data:str)->str:
  a=json.loads(data);z="commit-effect-root-v1"+self.f(str(len(a)))
  for x in a:z+=self.f(self.ef(x))
  return Keccak256(z.encode()).hexdigest()
 def el(self,e,q=False):
  r=e[14]if q else None
  a=(e[0],r[1]if r else e[1],str(r[2]if r else e[2]),r[3]if r else e[3],r[4]if r else e[4],str(r[6]if r else e[5]),e[6],str(e[7]),r[7]if r else e[8],r[8]if r else e[9],e[10],str(r[9]if r else e[11]),str(r[10]if r else e[12]))
  return Keccak256(("commit-evidence-leaf-v2"+"".join(self.f(x)for x in a)).encode()).hexdigest()
 @gl.public.view
 def evidence_root(self,data:str,active:bool)->str:
  a=json.loads(data);z="commit-evidence-root-v2"+self.f(str(len(a)))
  for x in a:z+=self.f(self.el(x,active))
  return Keccak256(z.encode()).hexdigest()
 def bad(self,e,r,v,c,m,ver):return {"outcome":"REPAIR_REQUIRED","failure_code":c,"evidence_id":e,"record_id":r,"record_version":v,"mission_id":m,"mission_version":ver}
 @gl.public.view
 def evaluate(self,meta:str,responses:str)->dict:
  x=json.loads(meta);rr=json.loads(responses);mid,ver,obj,pol,it,er,evr,aer,ss,ids=x;ok=True
  if len(rr)!=len(ss):raise E("response count")
  for n,s in enumerate(ss):
   ei,ai,u,h,ex,ri,rv=s;z=rr[n]
   if z[0]!=200:return self.bad(ei,ri,rv,"source_unavailable",mid,ver)
   if z[1]is None:return self.bad(ei,ri,rv,"response_body_missing",mid,ver)
   try:b=bytes.fromhex(z[1])
   except:return self.bad(ei,ri,rv,"response_body_missing",mid,ver)
   if len(b)>16384:return self.bad(ei,ri,rv,"record_too_large",mid,ver)
   def O(a):
    d={}
    for k,v in a:
     if k in d:raise E("json")
     d[k]=v
    return d
   def C(a):raise E("json")
   try:r=json.loads(b.decode(),object_pairs_hook=O,parse_constant=C)
   except:return self.bad(ei,ri,rv,"invalid_json",mid,ver)
   if not isinstance(r,dict):return self.bad(ei,ri,rv,"unsupported_record",mid,ver)
   if r.get("schema")!=S:return self.bad(ei,ri,rv,"unsupported_schema",mid,ver)
   if set(r)!={"schema","evidence_id","authority_id","url","subject","expires_at","mission_id","objective","policy_digest","policy_rule","intent_digest","effect_root","payload"}:return self.bad(ei,ri,rv,"unsupported_record",mid,ver)
   q={"evidence_id":ei,"authority_id":ai,"url":u,"subject":mid,"expires_at":ex,"mission_id":mid,"objective":obj,"policy_digest":pol,"policy_rule":R,"intent_digest":it,"effect_root":er}
   if any(type(r.get(k))is not type(v)or r.get(k)!=v for k,v in q.items()):return self.bad(ei,ri,rv,"snapshot_mismatch",mid,ver)
   p=r.get("payload")
   if not isinstance(p,dict)or set(p)!={"eligible","reason_code","effect_claims"}or type(p.get("eligible"))is not bool or type(p.get("reason_code"))is not str or not p["reason_code"]:return self.bad(ei,ri,rv,"invalid_payload",mid,ver)
   z=p["reason_code"]
   if len(z)>128 or any(ord(c)<32 or ord(c)>126 for c in z):return self.bad(ei,ri,rv,"invalid_payload",mid,ver)
   c=p.get("effect_claims")
   if not isinstance(c,dict)or set(c)!=set(ids):return self.bad(ei,ri,rv,"snapshot_mismatch",mid,ver)
   for f in ids:
    if type(c.get(f))is not bool:return self.bad(ei,ri,rv,"invalid_payload",mid,ver)
    if not c[f]:ok=False
   if Keccak256(json.dumps(p,ensure_ascii=True,sort_keys=True,separators=(",",":")).encode()).hexdigest()!=h:return self.bad(ei,ri,rv,"payload_hash_mismatch",mid,ver)
   if not p["eligible"]:ok=False
  return {"outcome":"DECISION","decision":"COMMIT"if ok else"ABORT","reason_code":"all_sources_and_effects_eligible"if ok else"policy_or_source_ineligible","mission_id":mid,"revision":V,"intent_digest":it,"policy_digest":pol,"policy_rule":R,"effect_root":er,"evidence_root":evr,"active_evidence_root":aer,"effect_count":len(ids),"evidence_count":len(ss)}
 @gl.public.view
 def fmt(self,kind:int,data:str)->dict:
  x=json.loads(data)
  if kind==0:
   i,m=x;return {"mission_id":i,"principal":m[0],"state":m[1],"version":m[21],"objective":m[2],"policy_digest":m[3],"intent_digest":m[4],"effect_root":m[5],"evidence_root":m[6],"policy_rule":R,"budget":m[7],"funded_value":m[8],"prepared_value":m[9],"refund_beneficiary":m[10],"effect_count":len(m[24]),"evidence_count":len(m[25]),"supplier_count":m[23],"decision":m[15],"reason_code":m[16],"decision_nonce":m[12],"evaluation_evidence_root":m[13],"allocation_applied":m[14],"refund_entitlement":m[11],"evaluation_count":m[17],"prepare_deadline":m[18],"recovery_deadline":m[19],"created_at":m[20]}
  if kind==1:
   i,m,ch,co=x;return {"receipt_schema":"commit-mission-receipt-v2","manifest_schema":"commit-mission-manifest-v2","protocol":"commit","revision":V,"chain_id":ch,"coordinator":co,"mission_id":i,"principal":m[0],"version":m[21],"objective":m[2],"state":m[1],"decision":m[15],"reason_code":m[16],"decision_nonce":m[12],"policy_rule":R,"policy_digest":m[3],"intent_digest":m[4],"effect_root":m[5],"evidence_root":m[6],"evaluation_evidence_root":m[13],"effect_count":len(m[24]),"evidence_count":len(m[25]),"budget":m[7],"funded_value":m[8],"prepared_value":m[9],"refund_beneficiary":m[10],"refund_entitlement":m[11],"prepare_deadline":m[18],"recovery_deadline":m[19],"evaluation_count":m[17],"allocation_applied":m[14],"external_withdrawal_recovery":False}
  if kind==2:
   i,q=x;return {"withdrawal_id":i,"mission_id":q[0],"beneficiary":q[1],"amount":q[2],"status":q[3]}
  if kind==3:
   f=x;return {"status":f[0],"failure_code":f[1],"evidence_id":f[2],"record_id":f[3],"failed_record_version":f[4],"mission_version":f[5],"attempt":f[6]}
  if kind==4:
   r=x;return {"status":r[0],"authority_id":r[1],"authority_version":r[2],"issuer_address":self.A(r[3]),"record_id":r[4],"original_record_version":r[5],"active_record_version":r[6],"url":r[7],"record_hash":r[8],"published_at":r[9],"expires_at":r[10]}
  if kind==5:
   i,f=x;return {"mission_id":i,"effect_id":f[0],"supplier":f[1],"digest":f[2],"dependency_id":f[3],"beneficiary":f[4],"value":f[5],"expiry":f[6]}
  if kind==6:
   i,a=x;return {"authority_id":i,"active":a[0],"host":a[1],"path_prefix":a[2],"issuer_address":self.A(a[3]),"authority_version":a[4]}
  if kind==7:
   t=x;return {"authority_id":t[0],"authority_version":t[1],"issuer_address":self.A(t[2]),"record_id":t[3],"record_version":t[4],"mission_id":t[5],"mission_version":t[6],"url":t[7],"record_hash":t[8],"published_at":t[9],"expires_at":t[10]}
  if kind==8:
   e=x;return {"mission_id":e[6],"evidence_id":e[0],"authority_id":e[1],"authority_version":e[2],"issuer_address":self.A(e[3]),"record_id":e[4],"record_version":e[5],"mission_version":e[7],"url":e[8],"record_hash":e[9],"subject":e[10],"published_at":e[11],"expires_at":e[12]}
  raise E("format kind")

 @gl.public.view
 def info(self,n:int)->dict:return {"protocol":"commit","revision":V,"custody_enabled":True,"semantic_evaluation_enabled":True,"equivalence_primitive":"run_nondet","decision_envelope":"commit-decision-v3","receipt_schema":"commit-mission-receipt-v2","manifest_schema":"commit-mission-manifest-v2","evaluation_trigger":"permissionless-after-seal","authority_provenance":"https-origin-path","mission_count":n,"external_withdrawal_recovery":False,"supplier_authorization_required":True,"effect_graph":"single-parent-acyclic","evidence_schema":S,"policy_rule":R,"policy_digest":P,"remote_body_limit":16384}
 @gl.public.view
 def manifest(self,data:str)->dict:
  i,m,ch,co,aa=json.loads(data);ad={x[0]:x[1]for x in aa};fs=[self.fmt(5,json.dumps([i,f],separators=(",",":")))for f in m[24]];es=[]
  for e in m[25]:
   q=self.fmt(8,json.dumps(e,separators=(",",":")));q["authority"]=self.fmt(6,json.dumps([e[1],ad[e[1]]],separators=(",",":")));es.append(q)
  return {"manifest_schema":"commit-mission-manifest-v2","protocol":"commit","revision":V,"chain_id":ch,"coordinator":co,"mission_id":i,"principal":m[0],"objective":m[2],"policy_rule":R,"policy_digest":m[3],"intent_digest":m[4],"state":m[1],"decision":m[15],"reason_code":m[16],"prepare_deadline":m[18],"recovery_deadline":m[19],"effect_count":len(m[24]),"evidence_count":len(m[25]),"effect_root":m[5],"evidence_root":m[6],"evaluation_evidence_root":m[13],"allocation_applied":m[14],"effects":fs,"evidence":es}
