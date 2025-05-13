import sys

sys.path.append("..")

import unittest

import sqlite3

import marshal

import time

from searchspace import *

import logging



# Configure basic logging to go to stdout
# You can customize the format, level, and destination (e.g., a file)
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(name)s:%(message)s', stream=sys.stdout)

# You can get a logger specific to your test module
log = logging.getLogger(__name__)

class TestSearchspace(unittest.TestCase):

    @classmethod
    def setUpClass(self):

        def t_opt(ds:dimset) -> bool:
            if ds.numindices > 1:
                ds.dimindices.pop()
                log.debug(f"~~~~ in optimizer for {ds.name()}, dimindices post opt: {ds.dimindices}")
                return True
            return False
            
        self.d1 = dimspec('d1', (-3,-2,-1,0,1,2,3))
        self.d2 = dimspec('d2', (-7,-6,-5,0,6,9,11))
        self.d4 = dimspec('d4', (90,80))
        self.d3 = dimspec('d3', ('a','b','c','d'))
        
        self.ds1 = dimset([self.d1,self.d2],[(0,0),(1,0),(0,1),(1,1),(2,2)])

        self.ds3 = dimset([self.d4], [(1,),(0,)])
        
        self.ds2 = dimset([self.d3], [(0,),(1,),(2,),(3,)], optimizer = t_opt)
        
        self.dsc = dimsetcol([self.ds1, self.ds3, self.ds2])

        def ttrig(ds:dimset):
            ds.acc[0] += 1
        
        self.ds1.trig = ttrig

        self.ds2.trig = ttrig

        # setup DB
        self.con = sqlite3.connect(':memory:')
        self.con.execute('''CREATE TABLE ss_test (
                         d1 INTEGER,
                         d2 INTEGER,
                         d4 INTEGER,
                         d3 INTEGER,
                         res TEXT
                         )
                         ''')
        self.con.execute('''
        CREATE TABLE dimsets (
        name TEXT PRIMARY KEY,
        indices BLOB,
        time INTEGER 
                   )       
                   ''')        
        self.con.commit()

        def savestate(state:dict):
        
            self.con.execute(f'''
            INSERT INTO ss_test (d1, d2, d4, d3)
            VALUES (?, ?, ?, ?)
            ''', tuple(state.values()) ) 
            self.con.commit()
        
        def loadstate() -> dict:
            s = self.con.execute("SELECT d1, d2, d4, d3 FROM ss_test ORDER BY rowid DESC LIMIT 1").fetchone()
            if not s: # if not previous attempts, start from the beginning
                return None
            else:
                return {'d1':s[0], 'd2':s[1], 'd4':s[2], 'd3':s[3]}

        def deldimset(name:str):
            self.con.execute("DELETE FROM dimsets WHERE name = ?", (name,))
            self.con.commit()
                    
        def loaddimset(name:str) -> dimset:
            ds = self.con.execute("SELECT indices FROM dimsets WHERE name = ? LIMIT 1", (name,)).fetchone()
            if ds:
                return marshal.loads(ds[0])
            return None

        def savedimset(name, dsi:list):
            ds = marshal.dumps(dsi)
            self.con.execute("REPLACE INTO dimsets VALUES (?, ?, ?)", (name, ds, int(time.time()) ))
            self.con.commit()

        self.dsc.setstorage({'savestate':savestate, 'loadstate':loadstate, 'deldimset':deldimset, 'loaddimset':loaddimset, 'savedimset':savedimset})
            

    def test1_names(self):
        print("Testing name strings")

        self.assertEqual(self.d1.dimname, 'd1')
        self.assertEqual(self.d2.dimname, 'd2')
        self.assertEqual(self.d3.dimname, 'd3')
        self.assertEqual(self.ds1.name(), 'd1d2_1')
        self.assertEqual(self.ds2.name(), 'd3_1')
        self.assertEqual(self.dsc.name(), 'd1d2d4d3')      
        

    def test2_trig(self):
        
        ds1v1 = next(self.ds1)
        ds1v2 = next(self.ds1)
        

        self.assertEqual(self.ds1.acc[0], 2, "Tested dimset trig via next(dimset)")

    def test3_currentresolve(self):
        print("##### Testing resolve of dims, dimsets and dimsetcol via resolve, next and current")
        self.ds1.resetpos()
        r1 = self.d1.resolve(0)
        r2 = self.d1.resolve(6)
        r3 = self.ds1.current()
        ds1_ci = self.ds1.current_indices()
        ds2_ci = self.ds2.current_indices()
        dsc_ci = self.dsc.resolve(mode = 'i')

     #   log.debug(f"--------current indices ds1: {ds1_ci}")
     #   log.debug(f"--------current indices ds2: {ds2_ci}")
     #   log.debug(f"--------current indices dsc: {dsc_ci}")

        
        self.assertEqual(dsc_ci, (0,0,1,0), "Testing current dimsetcol indices")

        self.assertEqual(ds1_ci, (0,0), "Testing current indices")
        self.assertEqual(ds2_ci, (0,), "Testing current indices")


        n = next(self.ds1)
        n2 = next(self.ds1)
        r4 = self.ds1.current()
        r4_ = self.ds1.current_dict()

        r5 = self.dsc.resolve()
        r5i = self.dsc.resolve(mode='i')
        next(self.ds2)
        r6 = self.dsc.resolve()
        r6i = self.dsc.resolve(mode='i')

        self.assertEqual(r1, -3)
        self.assertEqual(r2, 3)
        self.assertEqual(r3, (-3,-7))
        self.assertEqual(r3, n)
        self.assertNotEqual(r4, n2)
        self.assertEqual(r4, (-3,-6))
        self.assertEqual(r4_, {'d1':-3,'d2':-6})

        self.assertEqual(r5i, (0,1,1,0), """Testing resolve('i')""")
        

        self.assertEqual(r5, (-3,-6,80,'a'))
        self.assertEqual(r6, (-3,-6,80,'b'))
        self.assertEqual(r6i, (0,1,1,1), """Testing resolve('i')""")
        
        ds3cv = self.ds3.current()
        ds3ci = self.ds3.current_indices()

        self.assertEqual(ds3cv, (80,))
        self.assertEqual(ds3ci, (1,))


    def test4_process(self):
        self.dsc.reset()
        self.con.execute("DELETE FROM ss_test")

        self.assertEqual(self.dsc.resolve(mode='i'), (0,0,1,0), f"""Testing resolve on initial indices after reset
                         ds1.current_indices(): {self.ds1.current_indices()} ds1.index: {self.ds1.index},
                         ds3.current_indices(): {self.ds3.current_indices()} ds3.index: {self.ds3.index},
                         ds2.current_indices(): {self.ds2.current_indices()} ds2.index: {self.ds2.index}""")

        self.assertEqual(self.ds2.numindices, 4, "Checking ds2 numindices after reset()")

        self.dsc.process()

        self.assertEqual(self.dsc.col[2].acc[0], 16, 'Tested dimsetcol process, via optimizer and trig callback effects')



    def test5_store(self):
        
        res = self.con.execute('SELECT COUNT(*) FROM ss_test').fetchone()

        self.assertEqual(res[0], 16, "Tested number of state save records")

        res = self.con.execute('SELECT d1, d2, d4, d3 FROM ss_test ORDER BY rowid DESC LIMIT 1').fetchone()

        self.assertEqual(res, (2, 2, 0, 0), "Tested dims indices of final state save record") #  indices of dim values



    def test6_restore(self):

        def display_saveddimsets():
            dimsets = self.con.execute("SELECT name, indices FROM dimsets").fetchall()
            for ds in dimsets:
                name = ds[0]
                list = marshal.loads(ds[1])

                log.debug(f":::: dimset name: {name}, dimindices: {list}")
        states = self.con.execute("SELECT d1, d2, d4, d3 FROM ss_test").fetchall()
        s_str = "states: " + str(states)
    #    dimsets = self.con.execute("SELECT name, indices FROM dimsets").fetchall()
    #    ds_str = "\ndimsets: " + str(dimsets)    

        #log.debug(s_str + ds_str)

        print("###################### testing ####################")
        print(s_str)

        print(f"pre reset, ds2.numindices: {self.ds2.numindices}")
        display_saveddimsets()

        self.dsc.reset(clearstore=False)

        print(f"post reset, ds2.numindices: {self.ds2.numindices}")

        self.assertEqual(self.ds2.numindices, 4, "Checking dimset length after reset, pre restore")
        self.assertEqual(self.dsc.isend(), False, "Confirming not at end of dimsetcol, pre restore")

        self.dsc.restore()

        print(f"post restore, ds2.numindices: {self.ds2.numindices}")

        display_saveddimsets()

        self.assertEqual(self.ds2.numindices, 1, "Checking dimset length, post restore" ) # + s_str + ds_str
        self.assertEqual(self.dsc.resolve(mode='i'), (2,2,0,0), "Checking restored dimsetcol state, post restore" )

        # states stores indices, not if dimset iterations have reached end, so can't restore ended state directly
        # but we can skip restored state (which has already been processed), so if was the final state, 
        # the dimsetcol state would then return to end.
        # the skip is built into restore method
    
        self.assertEqual(self.dsc.isend(), True, "Confirming position at end of dimsetcol, post restore")
    
    def test7_process_by_iterator(self):

        self.dsc.reset()

        c = 0
        while next(self.dsc):
            c += 1
            print(f"\n{c} processing: dsc.curri.values(): {tuple(self.dsc.curri.values())}, resolve: {self.dsc.resolve(mode='i')}")
        self.assertEqual(tuple(self.dsc.curri.values()), (2,2,0,0))
        
if __name__ == '__main__':

 #   sys.stdout = sys.__stdout__
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestSearchspace))

#    runner = unittest.TextTestRunner(verbosity=2)
    # unittest.main(verbosity=2, buffer=False)
    runner = unittest.TextTestRunner(stream=sys.stdout, buffer=False, verbosity=2)

    # Run the tests
    runner.run(suite)