from pathlib import Path
import importlib, json
ROOT=Path(__file__).resolve().parents[1]

def test_contract_hardening_guards():
    s=(ROOT/'contracts/commit.py').read_text()
    assert 'if published_at>self.t():raise E("evidence published in future")' in s
    assert 'gl.message.sender_address!=gl.message.origin_address' in s
    assert 'r["helper_address"]=self.hh.as_hex' in s

def test_supported_transaction_rpc_only():
    s=(ROOT/'backend/live_reader.py').read_text()
    assert '"eth_getTransactionByHash"' in s
    assert '"gen_getTransactionReceipt"' not in s

class Q:
    def multi_items(self):
        return [('1','index'),('chain_id','61997'),('contract_address','0x'+'77'*20),('state_basis','FINALIZED')]
class U: path='/api/v1/index'
class R: query_params=Q(); url=U()

def test_vercel_capture_key_is_not_public_query_input():
    api=importlib.import_module('backend.service_api')
    assert api._public_query_items(R())==[('chain_id','61997'),('contract_address','0x'+'77'*20),('state_basis','FINALIZED')]

def test_exact_sdk_rc_and_security_headers():
    p=json.loads((ROOT/'package.json').read_text())
    assert p['dependencies']['genlayer-js']=='2.0.0-rc.1'
    n=(ROOT/'next.config.ts').read_text()
    for x in ('X-Content-Type-Options','X-Frame-Options','Referrer-Policy','Permissions-Policy'): assert x in n
