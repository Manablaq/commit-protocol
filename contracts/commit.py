# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }
from datetime import datetime ,timezone
import json
from genlayer import *
from genlayer .py .keccak import Keccak256
e0 =gl .vm .UserError
k0 ='mission not found'
k1 ='preparation deadline has passed'
k10 ='evidence_id'
k11 ='policy_rule'
k12 ='intent_digest'
k13 ='mission_version'
k14 ='evidence not found'
k15 ='effect_root'
k16 ='evaluation_evidence_root'
k17 ='authority_version'
k18 ='expires_at'
k19 ='decision'
k2 ='mission is not preparing'
k20 ='repair authority version mismatch'
k21 ='REPAIR_REQUIRED'
k22 ='active_evidence_root'
k23 ='objective'
k24 ='record_id'
k25 ='repair record identity mismatch'
k26 ='evidence attestation not found'
k27 ='evidence_count'
k28 ='issuer_address'
k29 ='record version'
k3 ='mission_id'
k30 ='record_version'
k31 ='allocation_applied'
k32 ='evidence_root'
k33 ='external_withdrawal_recovery'
k34 ='recovery deadline has passed'
k35 ='dependency effect not found'
k36 ='authority version'
k37 ='recovery_deadline'
k38 ='authority version mismatch'
k39 ='effect_count'
k4 ='reason_code'
k40 ='evidence failure not found'
k41 ='supplier is not authorized'
k42 ='mission already evaluated'
k43 ='outcome'
k44 ='prepare_deadline'
k45 ='manifest_schema'
k46 ='commit-evidence-leaf-v2'
k47 ='commit-evidence-root-v2'
k48 ='mission is underfunded'
k49 ='invalid evidence JSON'
k5 ='invalid authority host'
k50 ='mission is not sealed'
k51 ='failure_code'
k52 ='published_at'
k53 ='refund_beneficiary'
k54 ='refund_entitlement'
k55 ='revision'
k56 ='unsupported_record'
k57 ='record_hash'
k58 ='snapshot_mismatch'
k59 ='evaluation_count'
k6 ='invalid_payload'
k60 ='principal'
k61 ='record id'
k62 ='decision_nonce'
k63 ='owner required'
k64 ='prepared_value'
k65 ='receipt_schema'
k66 ='effect_claims'
k67 ='eligible'
k68 ='protocol'
k7 ='policy_digest'
k70 ='subject'
k8 ='authority_id'
k9 ='invalid authority path prefix'
PROTOCOL ='commit'
REVISION ='0.7.0-reviewable-manifest'
c15 ='PREPARING'
c16 ='SEALED'
c14 ='DECISION_PENDING'
c13 ='COMMITTED'
c12 ='ABORTED'
c17 ='DISPATCHED'
c7 =512
c3 =32
c4 =16
c5 =128
c6 =16 *1024
c8 =(1 <<256 )-1
c1 ='commit-evidence-v2'
c10 ='all-evidence-and-effects-v1'
c9 ='983307fac383ac4a92be6c0c361ea8f3c9d9efa20ad5e6e8bc8dee932f2a6103'
c0 ='commit-decision-v3'
c11 ='commit-mission-receipt-v2'
c2 ='commit-mission-manifest-v2'
@gl .evm .contract_interface
class _NativeRecipient :
 class View :
  pass
 class Write :
  pass
class CommitProtocol (gl .Contract ):
 s0 :Address
 s1 :u256
 s2 :TreeMap [str ,bool ]
 s3 :TreeMap [str ,str ]
 s4 :TreeMap [str ,Address ]
 s5 :TreeMap [str ,str ]
 s6 :TreeMap [str ,str ]
 s7 :TreeMap [str ,str ]
 s8 :TreeMap [str ,str ]
 s9 :TreeMap [str ,str ]
 s10 :TreeMap [str ,str ]
 s11 :TreeMap [str ,u256 ]
 s12 :TreeMap [str ,u256 ]
 s13 :TreeMap [str ,u256 ]
 s14 :TreeMap [str ,Address ]
 s15 :TreeMap [str ,u256 ]
 s16 :TreeMap [str ,str ]
 s17 :TreeMap [str ,str ]
 s18 :TreeMap [str ,bool ]
 s19 :TreeMap [str ,u256 ]
 s20 :TreeMap [str ,str ]
 s21 :TreeMap [str ,str ]
 s22 :TreeMap [str ,u256 ]
 s23 :TreeMap [str ,u256 ]
 s24 :TreeMap [str ,u256 ]
 s25 :TreeMap [str ,u256 ]
 s26 :TreeMap [str ,u256 ]
 s27 :TreeMap [str ,u256 ]
 s28 :TreeMap [str ,bool ]
 s29 :TreeMap [str ,str ]
 s30 :TreeMap [str ,Address ]
 s31 :TreeMap [str ,str ]
 s32 :TreeMap [str ,str ]
 s33 :TreeMap [str ,str ]
 s34 :TreeMap [str ,Address ]
 s35 :TreeMap [str ,u256 ]
 s36 :TreeMap [str ,u256 ]
 s37 :TreeMap [str ,str ]
 s38 :TreeMap [str ,bool ]
 s39 :TreeMap [str ,bool ]
 s40 :TreeMap [str ,str ]
 s41 :TreeMap [str ,str ]
 s42 :TreeMap [str ,Address ]
 s43 :TreeMap [str ,u256 ]
 s44 :TreeMap [str ,bool ]
 s45 :TreeMap [str ,u256 ]
 s46 :TreeMap [str ,bool ]
 s47 :TreeMap [str ,str ]
 s48 :TreeMap [str ,str ]
 s49 :TreeMap [str ,str ]
 s50 :TreeMap [str ,str ]
 s51 :TreeMap [str ,str ]
 s52 :TreeMap [str ,str ]
 s53 :TreeMap [str ,u256 ]
 s54 :TreeMap [str ,u256 ]
 s55 :TreeMap [str ,Address ]
 s56 :TreeMap [str ,str ]
 s57 :TreeMap [str ,u256 ]
 s58 :TreeMap [str ,u256 ]
 s59 :TreeMap [str ,u256 ]
 s60 :TreeMap [str ,str ]
 s61 :TreeMap [str ,bool ]
 s62 :TreeMap [str ,str ]
 s63 :TreeMap [str ,u256 ]
 s64 :TreeMap [str ,Address ]
 s65 :TreeMap [str ,str ]
 s66 :TreeMap [str ,u256 ]
 s67 :TreeMap [str ,str ]
 s68 :TreeMap [str ,u256 ]
 s69 :TreeMap [str ,str ]
 s70 :TreeMap [str ,str ]
 s71 :TreeMap [str ,u256 ]
 s72 :TreeMap [str ,u256 ]
 s73 :TreeMap [str ,u256 ]
 s74 :TreeMap [str ,bool ]
 s75 :TreeMap [str ,str ]
 s76 :TreeMap [str ,str ]
 s77 :TreeMap [str ,str ]
 s78 :TreeMap [str ,str ]
 s79 :TreeMap [str ,u256 ]
 s80 :TreeMap [str ,u256 ]
 s81 :TreeMap [str ,u256 ]
 s82 :TreeMap [str ,str ]
 s83 :TreeMap [str ,u256 ]
 s84 :TreeMap [str ,bool ]
 s85 :TreeMap [str ,str ]
 s86 :TreeMap [str ,str ]
 s87 :TreeMap [str ,u256 ]
 s88 :TreeMap [str ,Address ]
 s89 :TreeMap [str ,str ]
 s90 :TreeMap [str ,u256 ]
 s91 :TreeMap [str ,u256 ]
 s92 :TreeMap [str ,str ]
 s93 :TreeMap [str ,str ]
 s94 :TreeMap [str ,u256 ]
 s95 :TreeMap [str ,u256 ]
 s96 :TreeMap [str ,str ]
 s97 :TreeMap [str ,u256 ]
 s98 :TreeMap [str ,u256 ]
 s99 :u256
 s100 :TreeMap [str ,bool ]
 s101 :TreeMap [str ,str ]
 s102 :TreeMap [str ,Address ]
 s103 :TreeMap [str ,u256 ]
 s104 :TreeMap [str ,str ]
 def __init__ (self ):
  self .s0 =gl .message .sender_address
  self .s1 =0
  self .s99 =0
 def p0 (self ,value :str ,label :str )->None :
  if len (value )!=64 :
   raise e0 (f'{label } must be 32-byte lowercase hex')
  for v29 in value :
   if v29 not in '0123456789abcdef':
    raise e0 (f'{label } must be 32-byte lowercase hex')
 def p1 (self ,value :int ,label :str ,*,positive :bool =False )->int :
  if type (value )is not int or value <(1 if positive else 0 )or value >c8 :
   raise e0 (f'invalid {label }')
  return value
 def p2 (self ,value :int ,label :str )->int :
  if value <0 or value >=c8 :
   raise e0 (f'{label } overflow')
  return value +1
 def p3 (self ,value :str ,label :str ,limit :int =c7 )->None :
  if not value or len (value )>limit :
   raise e0 (f'invalid {label }')
  for v29 in value :
   if ord (v29 )<32 or ord (v29 )>126 :
    raise e0 (f'invalid {label }')
 def p4 (self ,value :str )->None :
  self .p3 (value ,'mission id')
  if ':'in value :
   raise e0 ('invalid mission id')
 def p5 (self ,value :str ,label :str ,limit :int )->None :
  self .p3 (value ,label ,limit )
  for v29 in value :
   if v29 not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_':
    raise e0 (f'invalid {label }')
 def p6 (self ,value :str )->None :
  self .p3 (value ,'authority host',253 )
  if value !=value .lower ()or any ((v29 in value for v29 in '/?:#@%\\')):
   raise e0 (k5 )
  if value .startswith ('.')or value .endswith ('.')or '..'in value :
   raise e0 (k5 )
  for label in value .split ('.'):
   if not 1 <=len (label )<=63 :
    raise e0 (k5 )
   if label [0 ]=='-'or label [-1 ]=='-':
    raise e0 (k5 )
   if any ((v29 not in 'abcdefghijklmnopqrstuvwxyz0123456789-'for v29 in label )):
    raise e0 (k5 )
 def p7 (self ,value :str )->None :
  self .p3 (value ,'authority path prefix',c7 )
  if not value .startswith ('/')or '//'in value or any ((v109 in value for v109 in ('?','#','%','\\'))):
   raise e0 (k9 )
  if value !='/'and value .endswith ('/'):
   raise e0 (k9 )
  if any ((v159 in ('.','..')for v159 in value .split ('/'))):
   raise e0 (k9 )
 def p8 (self ,url :str ,host :str ,path_prefix :str )->bool :
  try :
   self .p3 (url ,'evidence url',2048 )
  except Exception :
   return False
  v145 ='https://'+host
  if not url .startswith (v145 ):
   return False
  v155 =url [len (v145 ):]
  if not v155 .startswith ('/')or any ((v109 in v155 for v109 in ('?','#','%','\\'))):
   return False
  if v155 =='/':
   return path_prefix =='/'
  v160 =v155 .split ('/')
  if any ((v159 in ('','.','..')for v159 in v160 [1 :])):
   return False
  if path_prefix =='/':
   return True
  if v155 ==path_prefix :
   return True
  v27 =path_prefix if path_prefix .endswith ('/')else path_prefix +'/'
  return v155 .startswith (v27 )
 def p9 (self ,authority_id :str )->None :
  if not self .s38 .get (authority_id ,False ):
   raise e0 ('authority not found')
 def p10 (self ,value :Address ,label :str )->None :
  if value .as_hex =='0x'+'00'*20 :
   raise e0 (f'{label } cannot be zero')
 def p11 (self ,mission_id :str ,objective :str ,policy_digest :str ,budget :int ,refund_beneficiary :Address ,prepare_deadline :int ,recovery_deadline :int )->str :
  v98 =('2',PROTOCOL ,REVISION ,str (int (gl .message .chain_id )),gl .message .contract_address .as_hex ,mission_id ,objective ,policy_digest ,str (budget ),refund_beneficiary .as_hex ,str (prepare_deadline ),str (recovery_deadline ))
  v150 ='commit-intent-v2'+''.join ((self .p22 (v97 )for v97 in v98 ))
  return Keccak256 (v150 .encode ('utf-8')).hexdigest ()
 @gl .public .write
 def register_authority (self ,authority_id :str ,host :str ,path_prefix :str ,issuer_address :Address ,authority_version :int )->None :
  if gl .message .sender_address !=self .s0 :
   raise e0 (k63 )
  self .p5 (authority_id ,'authority id',64 )
  if self .s38 .get (authority_id ,False ):
   raise e0 ('authority already exists')
  self .p6 (host )
  self .p7 (path_prefix )
  self .p10 (issuer_address ,'issuer')
  self .p1 (authority_version ,k36 ,positive =True )
  self .s38 [authority_id ]=True
  self .s39 [authority_id ]=True
  self .s40 [authority_id ]=host
  self .s41 [authority_id ]=path_prefix
  self .s42 [authority_id ]=issuer_address
  self .s43 [authority_id ]=authority_version
 @gl .public .write
 def deactivate_authority (self ,authority_id :str )->None :
  if gl .message .sender_address !=self .s0 :
   raise e0 (k63 )
  self .p9 (authority_id )
  self .s39 [authority_id ]=False
 @gl .public .write
 def authorize_supplier (self ,mission_id :str ,supplier :Address )->None :
  self .p16 (mission_id )
  if self .s5 [mission_id ]!=c15 :
   raise e0 (k2 )
  if int (datetime .now (timezone .utc ).timestamp ())>int (self .s23 [mission_id ]):
   raise e0 (k1 )
  self .p10 (supplier ,'supplier')
  v165 =mission_id +':'+supplier .as_hex
  if self .s44 .get (v165 ,False ):
   raise e0 ('supplier already authorized')
  self .s44 [v165 ]=True
  self .s45 [mission_id ]=self .p2 (int (self .s45 .get (mission_id ,0 )),'supplier count')
 @gl .public .write
 def revoke_supplier (self ,mission_id :str ,supplier :Address )->None :
  self .p16 (mission_id )
  if self .s5 [mission_id ]!=c15 :
   raise e0 (k2 )
  if supplier ==self .s4 [mission_id ]:
   raise e0 ('principal cannot be revoked')
  v165 =mission_id +':'+supplier .as_hex
  if not self .s44 .get (v165 ,False ):
   raise e0 (k41 )
  for index in range (int (self .s27 [mission_id ])):
   effect_key =self .s37 [mission_id +':'+str (index )]
   if self .s30 [effect_key ]==supplier :
    raise e0 ('supplier has a prepared effect')
  self .s44 [v165 ]=False
  v34 =int (self .s45 .get (mission_id ,0 ))
  if v34 >0 :
   self .s45 [mission_id ]=v34 -1
 def p12 (self ,authority_id :str ,record_id :str ,record_version :int )->str :
  return authority_id +':'+record_id +':'+str (record_version )
 @gl .public .write
 def attest_evidence (self ,authority_id :str ,authority_version :int ,record_id :str ,record_version :int ,mission_id :str ,mission_version :int ,url :str ,record_hash :str ,published_at :int ,expires_at :int )->None :
  self .p9 (authority_id )
  if not self .s39 .get (authority_id ,False ):
   raise e0 ('authority is inactive')
  self .p1 (authority_version ,k36 ,positive =True )
  if authority_version !=int (self .s43 [authority_id ]):
   raise e0 (k38 )
  if gl .message .sender_address !=self .s42 [authority_id ]:
   raise e0 ('issuer required')
  self .p5 (record_id ,k61 ,c7 )
  self .p1 (record_version ,k29 ,positive =True )
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  self .p1 (mission_version ,'mission version',positive =True )
  if mission_version !=int (self .s26 [mission_id ]):
   raise e0 ('mission version mismatch')
  if not self .p8 (url ,self .s40 [authority_id ],self .s41 [authority_id ]):
   raise e0 ('evidence URL is outside authority')
  self .p0 (record_hash ,'record hash')
  self .p1 (published_at ,'evidence publication',positive =True )
  self .p1 (expires_at ,'evidence expiry',positive =True )
  v114 =int (self .s25 [mission_id ])
  if published_at <v114 :
   raise e0 ('evidence published before mission')
  if expires_at <int (self .s24 [mission_id ]):
   raise e0 ('invalid evidence expiry')
  v14 =self .p12 (authority_id ,record_id ,record_version )
  if self .s61 .get (v14 ,False ):
   raise e0 ('attestation already exists')
  self .s61 [v14 ]=True
  self .s62 [v14 ]=authority_id
  self .s63 [v14 ]=authority_version
  self .s64 [v14 ]=gl .message .sender_address
  self .s65 [v14 ]=record_id
  self .s66 [v14 ]=record_version
  self .s67 [v14 ]=mission_id
  self .s68 [v14 ]=mission_version
  self .s69 [v14 ]=url
  self .s70 [v14 ]=record_hash
  self .s71 [v14 ]=published_at
  self .s72 [v14 ]=expires_at
 @gl .public .write
 def register_evidence (self ,mission_id :str ,evidence_id :str ,authority_id :str ,authority_version :int ,record_id :str ,record_version :int )->None :
  self .p16 (mission_id )
  if self .s5 [mission_id ]!=c15 :
   raise e0 (k2 )
  if int (datetime .now (timezone .utc ).timestamp ())>int (self .s23 [mission_id ]):
   raise e0 (k1 )
  self .p5 (evidence_id ,'evidence id',c7 )
  evidence_key =mission_id +':'+evidence_id
  if self .s46 .get (evidence_key ,False ):
   raise e0 ('evidence already exists')
  v66 =int (self .s19 [mission_id ])
  if v66 >=c4 :
   raise e0 ('evidence limit exceeded')
  self .p9 (authority_id )
  self .p1 (authority_version ,k36 ,positive =True )
  self .p5 (record_id ,k61 ,c7 )
  self .p1 (record_version ,k29 ,positive =True )
  v14 =self .p12 (authority_id ,record_id ,record_version )
  if not self .s61 .get (v14 ,False ):
   raise e0 (k26 )
  if int (self .s63 [v14 ])!=authority_version :
   raise e0 (k38 )
  if self .s67 [v14 ]!=mission_id :
   raise e0 ('attestation mission mismatch')
  v37 =int (self .s26 [mission_id ])
  if int (self .s68 [v14 ])!=v37 :
   raise e0 ('attestation mission version mismatch')
  self .s46 [evidence_key ]=True
  self .s47 [evidence_key ]=mission_id
  self .s48 [evidence_key ]=evidence_id
  self .s49 [evidence_key ]=authority_id
  self .s54 [evidence_key ]=authority_version
  self .s55 [evidence_key ]=self .s64 [v14 ]
  self .s56 [evidence_key ]=record_id
  self .s57 [evidence_key ]=record_version
  self .s58 [evidence_key ]=v37
  self .s50 [evidence_key ]=self .s69 [v14 ]
  self .s51 [evidence_key ]=self .s70 [v14 ]
  self .s52 [evidence_key ]=mission_id
  self .s59 [evidence_key ]=self .s71 [v14 ]
  self .s53 [evidence_key ]=self .s72 [v14 ]
  self .s60 [mission_id +':'+str (v66 )]=evidence_key
  self .s19 [mission_id ]=self .p2 (v66 ,'evidence count')
 @gl .public .write
 def create_mission (self ,mission_id :str ,objective :str ,policy_digest :str ,budget :int ,refund_beneficiary :Address ,prepare_deadline :int ,recovery_deadline :int )->None :
  self .p4 (mission_id )
  self .p3 (objective ,k23 )
  self .p0 (policy_digest ,'policy digest')
  self .p1 (budget ,'mission budget',positive =True )
  self .p1 (prepare_deadline ,'preparation deadline',positive =True )
  self .p1 (recovery_deadline ,'recovery deadline',positive =True )
  if policy_digest !=c9 :
   raise e0 ('unsupported policy rule')
  if self .s2 .get (mission_id ,False ):
   raise e0 ('mission already exists')
  self .p10 (refund_beneficiary ,'refund beneficiary')
  if recovery_deadline <=prepare_deadline :
   raise e0 ('invalid deadline order')
  self .s2 [mission_id ]=True
  self .s4 [mission_id ]=gl .message .sender_address
  self .s5 [mission_id ]=c15
  self .s6 [mission_id ]=objective
  self .s7 [mission_id ]=policy_digest
  self .s8 [mission_id ]=self .p11 (mission_id ,objective ,policy_digest ,budget ,refund_beneficiary ,prepare_deadline ,recovery_deadline )
  self .s9 [mission_id ]=''
  self .s10 [mission_id ]=''
  self .s11 [mission_id ]=budget
  self .s12 [mission_id ]=0
  self .s13 [mission_id ]=0
  self .s14 [mission_id ]=refund_beneficiary
  self .s15 [mission_id ]=0
  self .s16 [mission_id ]=''
  self .s17 [mission_id ]=''
  self .s18 [mission_id ]=False
  self .s19 [mission_id ]=0
  self .s20 [mission_id ]=''
  self .s21 [mission_id ]=''
  self .s22 [mission_id ]=0
  self .s23 [mission_id ]=prepare_deadline
  self .s24 [mission_id ]=recovery_deadline
  self .s25 [mission_id ]=int (datetime .now (timezone .utc ).timestamp ())
  self .s26 [mission_id ]=1
  self .s27 [mission_id ]=0
  self .s44 [mission_id +':'+gl .message .sender_address .as_hex ]=True
  self .s45 [mission_id ]=1
  v129 =int (self .s1 )
  self .s3 [str (v129 )]=mission_id
  self .s1 =self .p2 (v129 ,'mission count')
 @gl .public .write .payable
 def fund_mission (self ,mission_id :str )->None :
  self .p16 (mission_id )
  if self .s5 [mission_id ]!=c15 :
   raise e0 (k2 )
  if int (datetime .now (timezone .utc ).timestamp ())>int (self .s23 [mission_id ]):
   raise e0 (k1 )
  amount =int (gl .message .value )
  if amount <=0 :
   raise e0 ('funding value must be positive')
  v101 =int (self .s12 [mission_id ])
  if v101 +amount >int (self .s11 [mission_id ]):
   raise e0 ('funding exceeds mission budget')
  self .s12 [mission_id ]=v101 +amount
 @gl .public .write
 def prepare_effect (self ,mission_id :str ,effect_id :str ,effect_digest :str ,beneficiary :Address ,value :int ,expiry :int )->None :
  self .p13 (mission_id ,effect_id ,effect_digest ,beneficiary ,value ,expiry ,'')
 @gl .public .write
 def prepare_effect_with_dependency (self ,mission_id :str ,effect_id :str ,effect_digest :str ,beneficiary :Address ,value :int ,expiry :int ,dependency_id :str )->None :
  self .p13 (mission_id ,effect_id ,effect_digest ,beneficiary ,value ,expiry ,dependency_id )
 def p13 (self ,mission_id :str ,effect_id :str ,effect_digest :str ,beneficiary :Address ,value :int ,expiry :int ,dependency_id :str )->None :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  if self .s5 [mission_id ]!=c15 :
   raise e0 (k2 )
  if int (datetime .now (timezone .utc ).timestamp ())>int (self .s23 [mission_id ]):
   raise e0 (k1 )
  self .p1 (value ,'effect value',positive =True )
  self .p1 (expiry ,'effect expiry',positive =True )
  v165 =mission_id +':'+gl .message .sender_address .as_hex
  if not self .s44 .get (v165 ,False ):
   raise e0 (k41 )
  if not effect_id or len (effect_id )>c7 or ':'in effect_id :
   raise e0 ('invalid effect id')
  self .p3 (effect_id ,'effect id')
  effect_key =mission_id +':'+effect_id
  if self .s28 .get (effect_key ,False ):
   raise e0 ('effect already exists')
  v44 =int (self .s27 [mission_id ])
  if v44 >=c3 :
   raise e0 ('effect limit exceeded')
  self .p0 (effect_digest ,'effect digest')
  if dependency_id :
   self .p5 (dependency_id ,'dependency id',c7 )
   if dependency_id ==effect_id :
    raise e0 ('effect cannot depend on itself')
   v39 =mission_id +':'+dependency_id
   if not self .s28 .get (v39 ,False ):
    raise e0 (k35 )
  self .p10 (beneficiary ,'effect beneficiary')
  if int (self .s13 [mission_id ])+value >int (self .s11 [mission_id ]):
   raise e0 ('prepared effects exceed mission budget')
  if expiry <int (self .s24 [mission_id ]):
   raise e0 ('invalid effect expiry')
  self .s28 [effect_key ]=True
  self .s29 [effect_key ]=mission_id
  self .s30 [effect_key ]=gl .message .sender_address
  self .s31 [effect_key ]=effect_id
  self .s32 [effect_key ]=effect_digest
  self .s33 [effect_key ]=dependency_id
  self .s34 [effect_key ]=beneficiary
  self .s35 [effect_key ]=value
  self .s36 [effect_key ]=expiry
  self .s13 [mission_id ]=int (self .s13 [mission_id ])+value
  self .s37 [mission_id +':'+str (v44 )]=effect_key
  self .s27 [mission_id ]=self .p2 (v44 ,'effect count')
 @gl .public .write
 def seal_mission (self ,mission_id :str ,effect_root :str ,evidence_root :str )->None :
  self .p16 (mission_id )
  if self .s5 [mission_id ]!=c15 :
   raise e0 (k2 )
  if int (datetime .now (timezone .utc ).timestamp ())>int (self .s23 [mission_id ]):
   raise e0 (k1 )
  if self .s27 [mission_id ]<=0 :
   raise e0 ('mission has no prepared effects')
  if self .s19 [mission_id ]<2 :
   raise e0 ('mission needs two evidence records')
  if self .s12 [mission_id ]<self .s13 [mission_id ]:
   raise e0 (k48 )
  if not self .p20 (mission_id ):
   raise e0 ('evidence authorities must be distinct')
  self .p21 (mission_id )
  self .p0 (effect_root ,'effect root')
  self .p0 (evidence_root ,'evidence root')
  if effect_root !=self .derive_effect_root (mission_id ):
   raise e0 ('effect root does not match prepared effects')
  if evidence_root !=self .derive_evidence_root (mission_id ):
   raise e0 ('evidence root does not match registered evidence')
  self .s9 [mission_id ]=effect_root
  self .s10 [mission_id ]=evidence_root
  self .s5 [mission_id ]=c16
 @gl .public .write
 def cancel_mission (self ,mission_id :str )->None :
  self .p16 (mission_id )
  if self .s5 [mission_id ]!=c15 :
   raise e0 ('sealed mission cannot be cancelled')
  self .p19 (mission_id ,'cancelled_by_principal')
 def p14 (self ,evidence_key :str ,attempt :int )->str :
  return evidence_key +':failure:'+str (attempt )
 def p15 (self ,evidence_key :str ,repair_index :int )->str :
  return evidence_key +':repair:'+str (repair_index )
 @gl .public .write
 def repair_evidence (self ,mission_id :str ,evidence_id :str ,authority_id :str ,authority_version :int ,record_id :str ,record_version :int )->None :
  self .p16 (mission_id )
  if self .s5 [mission_id ]!=c16 :
   raise e0 (k50 )
  if self .s20 [mission_id ]:
   raise e0 (k42 )
  v143 =int (datetime .now (timezone .utc ).timestamp ())
  if v143 >=int (self .s24 [mission_id ]):
   raise e0 (k34 )
  evidence_key =mission_id +':'+evidence_id
  if not self .s46 .get (evidence_key ,False ):
   raise e0 (k14 )
  v96 =self .s82 .get (evidence_key ,'')
  if not v96 or not self .s74 .get (v96 ,False ):
   raise e0 (k40 )
  if self .s75 [v96 ]!=k21 :
   raise e0 ('evidence is not repairable')
  if authority_id !=self .s49 [evidence_key ]:
   raise e0 ('repair authority mismatch')
  if authority_version !=int (self .s54 [evidence_key ]):
   raise e0 (k20 )
  if record_id !=self .s56 [evidence_key ]:
   raise e0 (k25 )
  self .p1 (record_version ,k29 ,positive =True )
  v38 =int (self .s57 [evidence_key ])
  v107 =self .s96 .get (evidence_key ,'')
  if v107 and self .s84 .get (v107 ,False ):
   v38 =int (self .s91 [v107 ])
  if record_version <=v38 :
   raise e0 ('repair record version must be newer')
  v14 =self .p12 (authority_id ,record_id ,record_version )
  if not self .s61 .get (v14 ,False ):
   raise e0 ('repair evidence attestation not found')
  if int (self .s63 [v14 ])!=authority_version :
   raise e0 (k20 )
  if self .s67 [v14 ]!=mission_id :
   raise e0 ('repair attestation mission mismatch')
  if int (self .s68 [v14 ])!=int (self .s26 [mission_id ]):
   raise e0 ('repair attestation mission version mismatch')
  if self .s65 [v14 ]!=self .s56 [evidence_key ]:
   raise e0 (k25 )
  if self .s64 [v14 ]!=self .s55 [evidence_key ]:
   raise e0 ('repair issuer mismatch')
  repair_index =int (self .s83 .get (evidence_key ,0 ))+1
  v156 =self .p15 (evidence_key ,repair_index )
  if self .s84 .get (v156 ,False ):
   raise e0 ('repair record already exists')
  self .s84 [v156 ]=True
  self .s85 [v156 ]='READY'
  self .s86 [v156 ]=authority_id
  self .s87 [v156 ]=authority_version
  self .s88 [v156 ]=self .s64 [v14 ]
  self .s89 [v156 ]=record_id
  self .s90 [v156 ]=int (self .s57 [evidence_key ])
  self .s91 [v156 ]=record_version
  self .s92 [v156 ]=self .s69 [v14 ]
  self .s93 [v156 ]=self .s70 [v14 ]
  self .s94 [v156 ]=self .s71 [v14 ]
  self .s95 [v156 ]=self .s72 [v14 ]
  self .s83 [evidence_key ]=repair_index
  self .s96 [evidence_key ]=v156
 @gl .public .write
 def evaluate_mission (self ,mission_id :str )->None :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  if self .s5 [mission_id ]!=c16 :
   raise e0 (k50 )
  if self .s20 [mission_id ]:
   raise e0 (k42 )
  v143 =int (datetime .now (timezone .utc ).timestamp ())
  if v143 >=int (self .s24 [mission_id ]):
   raise e0 (k34 )
  v161 =[]
  for index in range (int (self .s19 [mission_id ])):
   evidence_key =self .s60 [mission_id +':'+str (index )]
   authority_id =self .s49 [evidence_key ]
   url =self .s50 [evidence_key ]
   record_hash =self .s51 [evidence_key ]
   expires_at =int (self .s53 [evidence_key ])
   record_id =self .s56 [evidence_key ]
   record_version =int (self .s57 [evidence_key ])
   v156 =self .s96 .get (evidence_key ,'')
   if v156 and self .s84 .get (v156 ,False )and (self .s85 [v156 ]=='READY'):
    authority_id =self .s86 [v156 ]
    url =self .s92 [v156 ]
    record_hash =self .s93 [v156 ]
    expires_at =int (self .s95 [v156 ])
    record_id =self .s89 [v156 ]
    record_version =int (self .s91 [v156 ])
   v161 .append ((evidence_key ,self .s48 [evidence_key ],authority_id ,url ,record_hash ,expires_at ,record_id ,record_version ))
  v128 =mission_id
  v142 =int (self .s26 [mission_id ])
  v144 =self .s6 [mission_id ]
  v151 =self .s7 [mission_id ]
  v104 =self .s8 [mission_id ]
  v47 =self .s9 [mission_id ]
  v89 =self .s10 [mission_id ]
  v6 =self .derive_active_evidence_root (mission_id )
  v48 =[]
  for index in range (int (self .s27 [mission_id ])):
   effect_key =self .s37 [mission_id +':'+str (index )]
   v48 .append ((self .s31 [effect_key ],self .s33 .get (effect_key ,''),self .s32 [effect_key ],self .s34 [effect_key ].as_hex ,int (self .s35 [effect_key ]),int (self .s36 [effect_key ])))
  def f3 (evidence_id :str ,record_id :str ,record_version :int ,failure_code :str )->dict :
   return {k43 :k21 ,k51 :failure_code ,k10 :evidence_id ,k24 :record_id ,k30 :record_version ,k3 :v128 ,k13 :v142 }
  def f0 ()->dict :
   v8 =True
   for v2 ,evidence_id ,authority_id ,url ,v94 ,v93 ,record_id ,record_version in v161 :
    v157 =gl .nondet .web .get (url )
    if v157 .status !=200 :
     return f3 (evidence_id ,record_id ,record_version ,'source_unavailable')
    if not isinstance (v157 .body ,bytes ):
     return f3 (evidence_id ,record_id ,record_version ,'response_body_missing')
    if len (v157 .body )>c6 :
     return f3 (evidence_id ,record_id ,record_version ,'record_too_large')
    def f1 (pairs ):
     v149 ={}
     for v106 ,value in pairs :
      if v106 in v149 :
       raise e0 (k49 )
      v149 [v106 ]=value
     return v149
    def f2 (value ):
     raise e0 (k49 )
    try :
     v153 =json .loads (v157 .body .decode ('utf-8'),object_pairs_hook =f1 ,parse_constant =f2 )
    except (UnicodeDecodeError ,json .JSONDecodeError ,RecursionError ,e0 ):
     return f3 (evidence_id ,record_id ,record_version ,'invalid_json')
    if not isinstance (v153 ,dict ):
     return f3 (evidence_id ,record_id ,record_version ,k56 )
    if v153 .get ('schema')!=c1 :
     return f3 (evidence_id ,record_id ,record_version ,'unsupported_schema')
    v95 ={'schema',k10 ,k8 ,'url',k70 ,k18 ,k3 ,k23 ,k7 ,k11 ,k12 ,k15 ,'payload'}
    if set (v153 .keys ())!=v95 :
     return f3 (evidence_id ,record_id ,record_version ,k56 )
    if v153 .get (k10 )!=evidence_id or v153 .get (k8 )!=authority_id or v153 .get ('url')!=url or (v153 .get (k70 )!=v128 )or (type (v153 .get (k18 ))is not int )or (v153 .get (k18 )!=int (v93 ))or (v153 .get (k3 )!=v128 )or (v153 .get (k23 )!=v144 )or (v153 .get (k7 )!=v151 )or (v153 .get (k11 )!=c10 )or (v153 .get (k12 )!=v104 )or (v153 .get (k15 )!=v47 ):
     return f3 (evidence_id ,record_id ,record_version ,k58 )
    v150 =v153 .get ('payload')
    if not isinstance (v150 ,dict ):
     return f3 (evidence_id ,record_id ,record_version ,k6 )
    if set (v150 .keys ())!={k67 ,k4 ,k66 }:
     return f3 (evidence_id ,record_id ,record_version ,k6 )
    if type (v150 .get (k67 ))is not bool :
     return f3 (evidence_id ,record_id ,record_version ,k6 )
    if type (v150 .get (k4 ))is not str or not v150 [k4 ]:
     return f3 (evidence_id ,record_id ,record_version ,k6 )
    reason_code =v150 [k4 ]
    if len (reason_code )>c5 or any ((ord (v29 )<32 or ord (v29 )>126 for v29 in reason_code )):
     return f3 (evidence_id ,record_id ,record_version ,k6 )
    v41 =v150 .get (k66 )
    if not isinstance (v41 ,dict ):
     return f3 (evidence_id ,record_id ,record_version ,k6 )
    v92 ={v162 [0 ]for v162 in v48 }
    if set (v41 .keys ())!=v92 :
     return f3 (evidence_id ,record_id ,record_version ,k58 )
    v7 =True
    for effect_id ,v4 ,v1 ,v0 ,v5 ,v3 in v48 :
     if type (v41 .get (effect_id ))is not bool :
      return f3 (evidence_id ,record_id ,record_version ,k6 )
     if not v41 [effect_id ]:
      v7 =False
    v28 =json .dumps (v150 ,ensure_ascii =True ,sort_keys =True ,separators =(',',':'))
    v32 =Keccak256 (v28 .encode ('utf-8')).hexdigest ()
    if v32 !=v94 :
     return f3 (evidence_id ,record_id ,record_version ,'payload_hash_mismatch')
    if not v150 [k67 ]or not v7 :
     v8 =False
   return {k43 :'DECISION',k19 :'COMMIT'if v8 else 'ABORT',k4 :'all_sources_and_effects_eligible'if v8 else 'policy_or_source_ineligible',k3 :v128 ,k55 :REVISION ,k12 :v104 ,k7 :v151 ,k11 :c10 ,k15 :v47 ,k32 :v89 ,k22 :v6 ,k39 :len (v48 ),k27 :len (v161 )}
  def f4 (leader_result )->bool :
   if not isinstance (leader_result ,gl .vm .Return ):
    return False
   try :
    v166 =f0 ()
   except Exception :
    return False
   v108 =leader_result .calldata
   if not isinstance (v108 ,dict ):
    return False
   if v108 .get (k43 )!=v166 .get (k43 ):
    return False
   return v108 ==v166
  v158 =gl .vm .run_nondet (f0 ,f4 )
  if v158 .get (k43 )==k21 :
   evidence_key =mission_id +':'+v158 [k10 ]
   if not self .s46 .get (evidence_key ,False ):
    raise e0 ('repair evidence not found')
   attempt =int (self .s73 .get (evidence_key ,0 ))+1
   v96 =self .p14 (evidence_key ,attempt )
   self .s74 [v96 ]=True
   self .s75 [v96 ]=k21
   self .s76 [v96 ]=v158 [k51 ]
   self .s77 [v96 ]=v158 [k10 ]
   self .s78 [v96 ]=v158 [k24 ]
   self .s79 [v96 ]=v158 [k30 ]
   self .s80 [v96 ]=v158 [k13 ]
   self .s81 [v96 ]=attempt
   self .s73 [evidence_key ]=attempt
   self .s82 [evidence_key ]=v96
   return
  if v158 .get (k43 )!='DECISION':
   raise e0 ('invalid consensus outcome')
  if v158 [k19 ]not in ('COMMIT','ABORT'):
   raise e0 ('invalid consensus decision')
  self .s20 [mission_id ]=v158 [k19 ]
  self .s21 [mission_id ]=v158 [k4 ]
  self .s22 [mission_id ]=self .p2 (int (self .s22 [mission_id ]),'evaluation count')
  self .s17 [mission_id ]=v158 [k22 ]
  decision_nonce =Keccak256 ((c0 +self .p22 (mission_id )+self .p22 (str (int (self .s26 [mission_id ])))+self .p22 (v158 [k19 ])+self .p22 (v158 [k4 ])+self .p22 (self .s9 [mission_id ])+self .p22 (self .s10 [mission_id ])+self .p22 (v158 [k22 ])).encode ('utf-8')).hexdigest ()
  self .s16 [mission_id ]=decision_nonce
  self .s5 [mission_id ]=c14
  gl .get_contract_at (gl .message .contract_address ).emit (on ='finalized').apply_decision (mission_id ,decision_nonce )
 @gl .public .write
 def apply_decision (self ,mission_id :str ,decision_nonce :str )->None :
  if gl .message .sender_address !=gl .message .contract_address :
   raise e0 ('self message required')
  if self .s18 [mission_id ]:
   return
  if decision_nonce !=self .s16 [mission_id ]:
   raise e0 ('decision nonce mismatch')
  if self .s5 [mission_id ]!=c14 :
   raise e0 ('decision is not pending')
  if self .s20 [mission_id ]=='COMMIT':
   self .p18 (mission_id )
  elif self .s20 [mission_id ]=='ABORT':
   self .p19 (mission_id ,self .s21 [mission_id ])
  else :
   raise e0 ('invalid decision')
 @gl .public .write
 def claim_mission (self ,mission_id :str )->None :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  if self .s5 [mission_id ]not in (c13 ,c12 ):
   raise e0 ('mission is not allocated')
  beneficiary =gl .message .sender_address
  v30 =mission_id +':'+beneficiary .as_hex
  amount =int (self .s97 .get (v30 ,0 ))
  if amount <=0 :
   raise e0 ('no claimable balance')
  withdrawal_id =str (int (self .s99 ))
  if self .s100 .get (withdrawal_id ,False ):
   raise e0 ('withdrawal id collision')
  self .s97 [v30 ]=0
  v103 =beneficiary .as_hex
  v35 =int (self .s98 .get (v103 ,0 ))
  if v35 <amount :
   raise e0 ('claimable balance underflow')
  self .s98 [v103 ]=v35 -amount
  self .s100 [withdrawal_id ]=True
  self .s101 [withdrawal_id ]=mission_id
  self .s102 [withdrawal_id ]=beneficiary
  self .s103 [withdrawal_id ]=amount
  self .s104 [withdrawal_id ]=c17
  self .s99 =self .p2 (int (self .s99 ),'withdrawal count')
  _NativeRecipient (beneficiary ).emit_transfer (value =amount )
 @gl .public .write
 def expire_mission (self ,mission_id :str )->None :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  if self .s5 [mission_id ]not in (c15 ,c16 ,c14 ):
   raise e0 ('mission is already terminal')
  v143 =int (datetime .now (timezone .utc ).timestamp ())
  if v143 <int (self .s24 [mission_id ]):
   raise e0 ('recovery deadline has not passed')
  self .p19 (mission_id ,'recovery_deadline_expired')
 @gl .public .view
 def protocol_info (self )->dict :
  return {k68 :PROTOCOL ,k55 :REVISION ,'custody_enabled':True ,'semantic_evaluation_enabled':True ,'equivalence_primitive':'run_nondet','decision_envelope':c0 ,k65 :c11 ,k45 :c2 ,'evaluation_trigger':'permissionless-after-seal','authority_provenance':'https-origin-path','mission_count':int (self .s1 ),k33 :False ,'supplier_authorization_required':True ,'effect_graph':'single-parent-acyclic','evidence_schema':c1 ,k11 :c10 ,k7 :c9 ,'remote_body_limit':c6 }
 @gl .public .view
 def get_claimable (self ,beneficiary :Address )->int :
  return int (self .s98 .get (beneficiary .as_hex ,0 ))
 @gl .public .view
 def get_mission_claimable (self ,mission_id :str ,beneficiary :Address )->int :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  return int (self .s97 .get (mission_id +':'+beneficiary .as_hex ,0 ))
 @gl .public .view
 def get_mission_receipt (self ,mission_id :str )->dict :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  return {k65 :c11 ,k45 :c2 ,k68 :PROTOCOL ,k55 :REVISION ,'chain_id':int (gl .message .chain_id ),'coordinator':gl .message .contract_address .as_hex ,k3 :mission_id ,k60 :self .s4 [mission_id ].as_hex ,'version':int (self .s26 [mission_id ]),k23 :self .s6 [mission_id ],'state':self .s5 [mission_id ],k19 :self .s20 [mission_id ],k4 :self .s21 [mission_id ],k62 :self .s16 [mission_id ],k11 :c10 ,k7 :self .s7 [mission_id ],k12 :self .s8 [mission_id ],k15 :self .s9 [mission_id ],k32 :self .s10 [mission_id ],k16 :self .s17 [mission_id ],k39 :int (self .s27 [mission_id ]),k27 :int (self .s19 [mission_id ]),'budget':int (self .s11 [mission_id ]),'funded_value':int (self .s12 [mission_id ]),k64 :int (self .s13 [mission_id ]),k53 :self .s14 [mission_id ].as_hex ,k54 :int (self .s15 [mission_id ]),k44 :int (self .s23 [mission_id ]),k37 :int (self .s24 [mission_id ]),k59 :int (self .s22 [mission_id ]),k31 :self .s18 [mission_id ],k33 :False }
 @gl .public .view
 def get_withdrawal (self ,withdrawal_id :str )->dict :
  if not self .s100 .get (withdrawal_id ,False ):
   raise e0 ('withdrawal not found')
  return {'withdrawal_id':withdrawal_id ,k3 :self .s101 [withdrawal_id ],'beneficiary':self .s102 [withdrawal_id ].as_hex ,'amount':int (self .s103 [withdrawal_id ]),'status':self .s104 [withdrawal_id ]}
 @gl .public .view
 def get_withdrawal_count (self )->int :
  return int (self .s99 )
 @gl .public .view
 def get_withdrawal_by_index (self ,index :int )->dict :
  if index <0 or index >=int (self .s99 ):
   raise e0 ('withdrawal index out of range')
  return self .get_withdrawal (str (index ))
 @gl .public .view
 def derive_intent_digest (self ,mission_id :str )->str :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  return self .p11 (mission_id ,self .s6 [mission_id ],self .s7 [mission_id ],int (self .s11 [mission_id ]),self .s14 [mission_id ],int (self .s23 [mission_id ]),int (self .s24 [mission_id ]))
 def p16 (self ,mission_id :str )->None :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  if gl .message .sender_address !=self .s4 [mission_id ]:
   raise e0 ('principal required')
 def p17 (self ,mission_id :str ,beneficiary :Address ,amount :int )->None :
  if amount <=0 :
   return
  v30 =mission_id +':'+beneficiary .as_hex
  v115 =int (self .s97 .get (v30 ,0 ))
  v103 =beneficiary .as_hex
  v102 =int (self .s98 .get (v103 ,0 ))
  if amount >c8 -v115 :
   raise e0 ('mission claimable balance overflow')
  if amount >c8 -v102 :
   raise e0 ('global claimable balance overflow')
  self .s97 [v30 ]=v115 +amount
  self .s98 [v103 ]=v102 +amount
 def p18 (self ,mission_id :str )->None :
  v101 =int (self .s12 [mission_id ])
  v152 =int (self .s13 [mission_id ])
  if v101 <v152 :
   raise e0 (k48 )
  for index in range (int (self .s27 [mission_id ])):
   effect_key =self .s37 [mission_id +':'+str (index )]
   amount =int (self .s35 [effect_key ])
   self .p17 (mission_id ,self .s34 [effect_key ],amount )
  v154 =v101 -v152
  self .s15 [mission_id ]=v154
  self .p17 (mission_id ,self .s14 [mission_id ],v154 )
  self .s18 [mission_id ]=True
  self .s5 [mission_id ]=c13
 def p19 (self ,mission_id :str ,reason_code :str )->None :
  if self .s18 [mission_id ]:
   return
  v101 =int (self .s12 [mission_id ])
  self .s20 [mission_id ]='ABORT'
  self .s21 [mission_id ]=reason_code
  self .s15 [mission_id ]=v101
  self .p17 (mission_id ,self .s14 [mission_id ],v101 )
  self .s18 [mission_id ]=True
  self .s5 [mission_id ]=c12
 def p20 (self ,mission_id :str )->bool :
  v100 =self .s60 [mission_id +':0']
  v99 =self .s55 [v100 ]
  v33 =int (self .s19 [mission_id ])
  for index in range (1 ,v33 ):
   v106 =self .s60 [mission_id +':'+str (index )]
   if self .s55 [v106 ]!=v99 :
    return True
  return False
 def p21 (self ,mission_id :str )->None :
  v33 =int (self .s27 [mission_id ])
  for index in range (v33 ):
   v36 =self .s37 [mission_id +':'+str (index )]
   v167 =0
   while True :
    v147 =self .s33 .get (v36 ,'')
    if not v147 :
     break
    v148 =mission_id +':'+v147
    if not self .s28 .get (v148 ,False ):
     raise e0 (k35 )
    if self .s29 [v148 ]!=mission_id :
     raise e0 ('dependency mission mismatch')
    v167 +=1
    if v167 >=v33 :
     raise e0 ('effect graph contains a cycle')
    v36 =v148
 def p22 (self ,value :str )->str :
  return str (len (value ))+':'+value
 def p23 (self ,effect_key :str )->str :
  v98 =(self .s31 [effect_key ],self .s32 [effect_key ],self .s33 .get (effect_key ,''),self .s30 [effect_key ].as_hex ,self .s34 [effect_key ].as_hex ,str (int (self .s35 [effect_key ])),str (int (self .s36 [effect_key ])))
  v150 ='commit-effect-leaf-v1'+''.join ((self .p22 (v97 )for v97 in v98 ))
  return Keccak256 (v150 .encode ('utf-8')).hexdigest ()
 def p24 (self ,evidence_key :str )->str :
  v98 =(self .s48 [evidence_key ],self .s49 [evidence_key ],str (int (self .s54 [evidence_key ])),self .s55 [evidence_key ].as_hex ,self .s56 [evidence_key ],str (int (self .s57 [evidence_key ])),self .s47 [evidence_key ],str (int (self .s58 [evidence_key ])),self .s50 [evidence_key ],self .s51 [evidence_key ],self .s52 [evidence_key ],str (int (self .s59 [evidence_key ])),str (int (self .s53 [evidence_key ])))
  v150 =k46 +''.join ((self .p22 (v97 )for v97 in v98 ))
  return Keccak256 (v150 .encode ('utf-8')).hexdigest ()
 @gl .public .view
 def derive_effect_root (self ,mission_id :str )->str :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  v33 =int (self .s27 [mission_id ])
  v150 ='commit-effect-root-v1'+self .p22 (str (v33 ))
  for index in range (v33 ):
   effect_key =self .s37 [mission_id +':'+str (index )]
   v150 +=self .p22 (self .p23 (effect_key ))
  return Keccak256 (v150 .encode ('utf-8')).hexdigest ()
 def p25 (self ,evidence_key :str )->str :
  v156 =self .s96 .get (evidence_key ,'')
  if not v156 or not self .s84 .get (v156 ,False )or self .s85 [v156 ]!='READY':
   return self .p24 (evidence_key )
  v98 =(self .s48 [evidence_key ],self .s86 [v156 ],str (int (self .s87 [v156 ])),self .s88 [v156 ].as_hex ,self .s89 [v156 ],str (int (self .s91 [v156 ])),self .s47 [evidence_key ],str (int (self .s58 [evidence_key ])),self .s92 [v156 ],self .s93 [v156 ],self .s52 [evidence_key ],str (int (self .s94 [v156 ])),str (int (self .s95 [v156 ])))
  v150 =k46 +''.join ((self .p22 (value )for value in v98 ))
  return Keccak256 (v150 .encode ('utf-8')).hexdigest ()
 @gl .public .view
 def derive_active_evidence_root (self ,mission_id :str )->str :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  v33 =int (self .s19 [mission_id ])
  v150 =k47 +self .p22 (str (v33 ))
  for index in range (v33 ):
   evidence_key =self .s60 [mission_id +':'+str (index )]
   v150 +=self .p22 (self .p25 (evidence_key ))
  return Keccak256 (v150 .encode ('utf-8')).hexdigest ()
 @gl .public .view
 def derive_evidence_root (self ,mission_id :str )->str :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  v33 =int (self .s19 [mission_id ])
  v150 =k47 +self .p22 (str (v33 ))
  for index in range (v33 ):
   evidence_key =self .s60 [mission_id +':'+str (index )]
   v150 +=self .p22 (self .p24 (evidence_key ))
  return Keccak256 (v150 .encode ('utf-8')).hexdigest ()
 @gl .public .view
 def get_evidence_failure (self ,mission_id :str ,evidence_id :str )->dict :
  evidence_key =mission_id +':'+evidence_id
  if not self .s46 .get (evidence_key ,False ):
   raise e0 (k14 )
  v96 =self .s82 .get (evidence_key ,'')
  if not v96 or not self .s74 .get (v96 ,False ):
   raise e0 (k40 )
  return {'status':self .s75 [v96 ],k51 :self .s76 [v96 ],k10 :self .s77 [v96 ],k24 :self .s78 [v96 ],'failed_record_version':int (self .s79 [v96 ]),k13 :int (self .s80 [v96 ]),'attempt':int (self .s81 [v96 ])}
 @gl .public .view
 def get_evidence_repair (self ,mission_id :str ,evidence_id :str )->dict :
  evidence_key =mission_id +':'+evidence_id
  if not self .s46 .get (evidence_key ,False ):
   raise e0 (k14 )
  v156 =self .s96 .get (evidence_key ,'')
  if not v156 or not self .s84 .get (v156 ,False ):
   raise e0 ('evidence repair not found')
  return {'status':self .s85 [v156 ],k8 :self .s86 [v156 ],k17 :int (self .s87 [v156 ]),k28 :self .s88 [v156 ],k24 :self .s89 [v156 ],'original_record_version':int (self .s90 [v156 ]),'active_record_version':int (self .s91 [v156 ]),'url':self .s92 [v156 ],k57 :self .s93 [v156 ],k52 :int (self .s94 [v156 ]),k18 :int (self .s95 [v156 ])}
 @gl .public .view
 def get_mission (self ,mission_id :str )->dict :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  return {k3 :mission_id ,k60 :self .s4 [mission_id ].as_hex ,'state':self .s5 [mission_id ],'version':int (self .s26 [mission_id ]),k23 :self .s6 [mission_id ],k7 :self .s7 [mission_id ],k12 :self .s8 [mission_id ],k15 :self .s9 [mission_id ],k32 :self .s10 [mission_id ],k11 :c10 ,'budget':int (self .s11 [mission_id ]),'funded_value':int (self .s12 [mission_id ]),k64 :int (self .s13 [mission_id ]),k53 :self .s14 [mission_id ].as_hex ,k39 :int (self .s27 [mission_id ]),k27 :int (self .s19 [mission_id ]),'supplier_count':int (self .s45 .get (mission_id ,0 )),k19 :self .s20 [mission_id ],k4 :self .s21 [mission_id ],k62 :self .s16 [mission_id ],k16 :self .s17 [mission_id ],k31 :self .s18 [mission_id ],k54 :int (self .s15 [mission_id ]),k59 :int (self .s22 [mission_id ]),k44 :int (self .s23 [mission_id ]),k37 :int (self .s24 [mission_id ]),'created_at':int (self .s25 [mission_id ])}
 @gl .public .view
 def get_mission_by_index (self ,index :int )->dict :
  if index <0 or index >=int (self .s1 ):
   raise e0 ('mission index out of range')
  return self .get_mission (self .s3 [str (index )])
 @gl .public .view
 def get_effect (self ,mission_id :str ,effect_id :str )->dict :
  effect_key =mission_id +':'+effect_id
  if not self .s28 .get (effect_key ,False ):
   raise e0 ('effect not found')
  if self .s29 [effect_key ]!=mission_id :
   raise e0 ('effect mission mismatch')
  return {k3 :mission_id ,'effect_id':effect_id ,'supplier':self .s30 [effect_key ].as_hex ,'digest':self .s32 [effect_key ],'dependency_id':self .s33 .get (effect_key ,''),'beneficiary':self .s34 [effect_key ].as_hex ,'value':int (self .s35 [effect_key ]),'expiry':int (self .s36 [effect_key ])}
 @gl .public .view
 def get_effect_by_index (self ,mission_id :str ,index :int )->dict :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  if index <0 or index >=int (self .s27 [mission_id ]):
   raise e0 ('effect index out of range')
  effect_key =self .s37 [mission_id +':'+str (index )]
  return self .get_effect (mission_id ,self .s31 [effect_key ])
 @gl .public .view
 def get_authority (self ,authority_id :str )->dict :
  self .p9 (authority_id )
  return {k8 :authority_id ,'active':self .s39 .get (authority_id ,False ),'host':self .s40 [authority_id ],'path_prefix':self .s41 [authority_id ],k28 :self .s42 [authority_id ],k17 :int (self .s43 [authority_id ])}
 @gl .public .view
 def authorities_are_independent (self ,authority_a :str ,authority_b :str )->bool :
  self .p9 (authority_a )
  self .p9 (authority_b )
  if authority_a ==authority_b :
   return False
  return self .s42 [authority_a ]!=self .s42 [authority_b ]
 @gl .public .view
 def get_evidence_attestation (self ,authority_id :str ,record_id :str ,record_version :int )->dict :
  self .p9 (authority_id )
  self .p5 (record_id ,k61 ,c7 )
  self .p1 (record_version ,k29 ,positive =True )
  v14 =self .p12 (authority_id ,record_id ,record_version )
  if not self .s61 .get (v14 ,False ):
   raise e0 (k26 )
  return {k8 :self .s62 [v14 ],k17 :int (self .s63 [v14 ]),k28 :self .s64 [v14 ],k24 :self .s65 [v14 ],k30 :int (self .s66 [v14 ]),k3 :self .s67 [v14 ],k13 :int (self .s68 [v14 ]),'url':self .s69 [v14 ],k57 :self .s70 [v14 ],k52 :int (self .s71 [v14 ]),k18 :int (self .s72 [v14 ])}
 @gl .public .view
 def get_evidence (self ,mission_id :str ,evidence_id :str )->dict :
  evidence_key =mission_id +':'+evidence_id
  if not self .s46 .get (evidence_key ,False ):
   raise e0 (k14 )
  if self .s47 [evidence_key ]!=mission_id :
   raise e0 ('evidence mission mismatch')
  return {k3 :mission_id ,k10 :evidence_id ,k8 :self .s49 [evidence_key ],k17 :int (self .s54 [evidence_key ]),k28 :self .s55 [evidence_key ],k24 :self .s56 [evidence_key ],k30 :int (self .s57 [evidence_key ]),k13 :int (self .s58 [evidence_key ]),'url':self .s50 [evidence_key ],k57 :self .s51 [evidence_key ],k70 :self .s52 [evidence_key ],k52 :int (self .s59 [evidence_key ]),k18 :int (self .s53 [evidence_key ])}
 @gl .public .view
 def get_evidence_by_index (self ,mission_id :str ,index :int )->dict :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  if index <0 or index >=int (self .s19 [mission_id ]):
   raise e0 ('evidence index out of range')
  evidence_key =self .s60 [mission_id +':'+str (index )]
  return self .get_evidence (mission_id ,self .s48 [evidence_key ])
 @gl .public .view
 def get_mission_manifest (self ,mission_id :str )->dict :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  v51 =[]
  for index in range (int (self .s27 [mission_id ])):
   v51 .append (self .get_effect_by_index (mission_id ,index ))
  v52 =[]
  for index in range (int (self .s19 [mission_id ])):
   v105 =self .get_evidence_by_index (mission_id ,index )
   v105 ['authority']=self .get_authority (v105 [k8 ])
   v52 .append (v105 )
  return {k45 :c2 ,k68 :PROTOCOL ,k55 :REVISION ,'chain_id':int (gl .message .chain_id ),'coordinator':gl .message .contract_address .as_hex ,k3 :mission_id ,k60 :self .s4 [mission_id ].as_hex ,k23 :self .s6 [mission_id ],k11 :c10 ,k7 :self .s7 [mission_id ],k12 :self .s8 [mission_id ],'state':self .s5 [mission_id ],k19 :self .s20 [mission_id ],k4 :self .s21 [mission_id ],k44 :int (self .s23 [mission_id ]),k37 :int (self .s24 [mission_id ]),k39 :int (self .s27 [mission_id ]),k27 :int (self .s19 [mission_id ]),k15 :self .s9 [mission_id ],k32 :self .s10 [mission_id ],k16 :self .s17 [mission_id ],k31 :self .s18 [mission_id ],'effects':v51 ,'evidence':v52 }
 @gl .public .view
 def is_supplier_authorized (self ,mission_id :str ,supplier :Address )->bool :
  if not self .s2 .get (mission_id ,False ):
   raise e0 (k0 )
  return self .s44 .get (mission_id +':'+supplier .as_hex ,False )
