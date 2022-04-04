from builtins import set
import unittest

from graph import DCRChoreography, DCRProjection, DCRGraph

class TestParser(unittest.TestCase):

    def setUp(self):
        self.graph = DCRGraph().from_xml("input/data_test.xml")
        #self.projection = self.choreography.project_for_actor("a")

        # Make a dummy projection.
        self.projection = DCRProjection.from_data("a", dict(), set(), set(), set(), set(), set(),set(),set(),collapse = False)

        #self.projection = DCRProjection.from_data("a", dict(), g.Nodes, set(), set(), set(), set(),set(),set(),collapse = False)
        #from_data(actor, mapping, activities, connections, included, pending, executed,users,services,collapse = True):


    def test_sth(self):
        # Parse a graph specifically for tests and check if the 
        
        self.assertIsInstance(self.graph, DCRGraph)
        #print (graph)
        
        # graph, DCRChoreography)
        #print (graph)


if __name__ == '__main__':
    unittest.main()

    target = __import__("../graph.py")

