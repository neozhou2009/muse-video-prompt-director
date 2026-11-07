import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from validate_source_delivery import validate


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.source = {'items': [
            {'id':'p','field':'performance','source_location':'导演 S1','text':'握紧手'},
            {'id':'r','field':'reaction','source_location':'导演 S1','text':'看他的手'},
            {'id':'d','field':'dialogue','source_location':'剧本 S1','text':'别动。'},
        ]}
        self.delivery = {'clips':[{'id':'c','visible_cast':['甲','乙'],'prompt':'甲握紧手。乙看他的手。甲说：别动。'}],
                         'decisions':[
            {'source_id':'p','status':'included','reason':'在画','evidence':[{'clip_id':'c','time_window':'0—2','excerpt':'握紧手','actors':['甲']}]},
            {'source_id':'r','status':'included','reason':'在画','evidence':[{'clip_id':'c','time_window':'2—3','excerpt':'看他的手','actors':['乙']}]},
            {'source_id':'d','status':'included','reason':'原句','evidence':[{'clip_id':'c','time_window':'3—5','excerpt':'别动。','actors':[]}]},
        ]}

    def test_valid(self):
        self.assertEqual(validate(self.source, self.delivery)['source_items'], 3)

    def test_missing_decision(self):
        self.delivery['decisions'].pop(1)
        with self.assertRaises(ValueError): validate(self.source, self.delivery)

    def test_missing_prompt_text(self):
        self.delivery['clips'][0]['prompt'] = '表演：握紧手。反应：。甲说：别动。'
        with self.assertRaises(ValueError): validate(self.source, self.delivery)

    def test_offscreen_reaction(self):
        self.delivery['clips'][0]['visible_cast'] = ['甲']
        with self.assertRaises(ValueError): validate(self.source, self.delivery)

    def test_dialogue_not_exact(self):
        self.delivery['clips'][0]['prompt'] += '别走。'
        self.delivery['decisions'][2]['evidence'][0]['excerpt'] = '别走。'
        with self.assertRaises(ValueError): validate(self.source, self.delivery)

    def test_split_dialogue(self):
        self.delivery['clips'] = [{'id':'c1','visible_cast':['甲','乙'],'prompt':'握紧手。看他的手。别'}, {'id':'c2','visible_cast':['甲'],'prompt':'动。'}]
        for d in self.delivery['decisions'][:2]: d['evidence'][0]['clip_id']='c1'
        self.delivery['decisions'][2]['evidence'] = [
            {'clip_id':'c1','time_window':'3—5','excerpt':'别','actors':[]},
            {'clip_id':'c2','time_window':'0—1','excerpt':'动。','actors':[]}]
        self.assertEqual(validate(self.source,self.delivery)['status'], 'passed')
        self.delivery['decisions'][2]['evidence'].reverse()
        with self.assertRaises(ValueError): validate(self.source,self.delivery)

    def test_unauthorized_deletion(self):
        self.delivery['decisions'][1] = {'source_id':'r','status':'omitted','reason':'删掉'}
        with self.assertRaises(ValueError): validate(self.source,self.delivery)
        self.delivery['decisions'][1]['user_authorization'] = '用户要求删去该反应'
        self.assertEqual(validate(self.source,self.delivery)['status'], 'passed')

    def test_not_applicable_needs_reason(self):
        self.delivery['decisions'][1] = {'source_id':'r','status':'not_applicable','reason':'空镜无人物'}
        self.assertEqual(validate(self.source,self.delivery)['status'], 'passed')
        self.delivery['decisions'][1]['reason'] = ''
        with self.assertRaises(ValueError): validate(self.source,self.delivery)

    def test_duplicate_source(self):
        self.source['items'].append(copy.deepcopy(self.source['items'][0]))
        with self.assertRaises(ValueError): validate(self.source,self.delivery)


if __name__ == '__main__': unittest.main()
