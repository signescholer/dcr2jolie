# coding=utf-8
"""
This module contains the DCR graph representation. It also contains the XML format parsing functionality
"""
import os
import xml.etree.ElementTree as Etree
import re

from activity import DCRActivityBase, DCRActivityNest, DCRActivity, DCREndpointActivity, DCRInteractionActivity
from conn import DCRConnection, Condition, Response, CoResponse, Include, Exclude, Milestone
from collections import defaultdict

class DCRGraph(object):
    """ # modified
    The representation of a DCR graph
    """

    # Recursive pretty print of the graph structure
    def str_node(self,node,indent):
        """ #own """
        return "\n"+"    "*indent+node.str_name()+''.join(["\n"+"    "*(indent)+"<-"+str(c) for c in self.Connections if c.EndNode == node])+''.join(["\n"+"    "*(indent)+"->"+str(c) for c in self.Connections if c.StartNode == node])+" (" + ', '.join([self.str_node(n,indent+1) for n in (node.Activities if node.isNest else [])]) + ")"

    def __str__(self):
        """#own
        Recursive pretty print of the graph."""
        ret = ""
        for node in [n for n in self.Nodes if n.Parent == None]:
            ret += "\n" + self.str_node(node,0)
        return ret

    def __init__(self):
        """Constructor for the DCR Graph"""
        # Set up instance variables
        self.Connections = set()
        self.Mappings = {}
        self.Nodes = set()
        self.ConditionTargets = set()
        self.MilestoneTargets = set()
        self.InitialIncluded = set()
        self.InitialPending = set()
        self.InitialExecuted = set()

    @classmethod
    def from_xml(cls,xml_path):
        """#own
        Initiate a DCR graph from XML.
        """
        graph = cls()
        graph.parse(xml_path)
        return graph

    @classmethod
    def from_data(cls, mapping, activities, connections, included, pending, executed):
        """ #own
        Initiate a DCR graph from an already parsed DCR graph.
        :param mapping: The mapping of labels to events.
        :param activities: A list of activities.
        :param connections: A list of connections.
        :param included: Part of the marking. Included events.
        :param pending: Part of the marking. Pending events.
        :param executed: Part of the marking. Executed events.
        :return: DCRGraph
        """
        graph = cls()

        graph.Mappings = mapping

        graph.Nodes = activities

        graph.Connections = connections

        graph.InitialIncluded = included
        graph.InitialPending = pending
        graph.InitialExecuted = executed

        return graph

    def parse(self, xml_path):
        # Init XML reader for class
        dcr_xml = Etree.parse(xml_path)
        dcr_xml_root = dcr_xml.getroot()

        # Start parsing the DCR Graph xml
        self.parse_label_mapping(dcr_xml_root)
        self.parse_activities(dcr_xml_root)
        self.parse_connections(dcr_xml_root)
        self.parse_initial_marking(dcr_xml_root)

    def parse_label_mapping(self,dcr_xml_root):
        """
        In DCR-Graph xml the activity label and id have to be matched to relate them
        :return: a dict with related mappings
        """
        mappings = {}
        for mapping in dcr_xml_root.iter('labelMapping'):
            mappings[mapping.get('eventId')] = mapping.get('labelId')
        self.Mappings = mappings

    def make_event(self,event_id, event_name):
        """ #own
        Makes a DCRActivity.
        Made to be overridden to make DCRInteractionActivity in choreographies and end-points.
        :param event_id: Id of the event.
        :param event_name: Label of the event.
        :return: The activity object.
        """
        return DCRActivity(event_id, event_name)

    def handle_roles(self,node,event):
        """ #own
        Handles parsing of roles.
        Made to be overridden in DCRInteractionGraph.
        :param node: The node to add the roles to.
        :param event: The xml event containing string of the roles.
        """
        roles = set()
        for role in event.iter('role'):
            if role.text is not None:
                roles.add(role.text)

        node.set_roles(roles)


    def parse_xml_event(self,event):
        """ #modified to add datatype and handle roles.
        Adds an event to the graph
        :param event: The event to be added
        """

        event_id: str = event.get('id')
        event_name = self.Mappings.get(event_id)

        node = self.make_event(event_id, event_name)

        datatype_field = event.find('custom').find('eventData').find('dataType')
        node.set_datatype( datatype_field.text if datatype_field is not None else "")

        self.handle_roles(node,event)

        self.Nodes.add(node)

    def parse_xml_nest(self, nest):
        """ #modified to handle recursive nesting.
        Adds a nested activity to the DCR Graph
        :param nest: The root of the nested activity
        """
        sub_events = set()
        activities = set()

        # First add all sub_events.
        for event in nest.findall('event'):
            self.parse_event_or_nest(event)
            sub_events.add(event.get('id'))

        event_id: str = nest.get('id')
        event_name = self.Mappings.get(event_id)
        
        for activity in sub_events:
            activities.add(self.get_event(activity))

        nest_node = DCRActivityNest(event_id, event_name, activities)

        self.Nodes.add(nest_node)

    def parse_event_or_nest(self,event):
        """ #own
        Wrapper for parse_xml_nest and parse_xml_event.
        Determines whether param 'event' is a nest or not, and calls the proper parse function.
        :param event: The event or event nest to be added.
        """
        if len(event.findall('event')) > 0: # If it has children.
            self.parse_xml_nest(event)
        else:
            self.parse_xml_event(event)

    def parse_activities(self,dcr_xml_root):
        """ #modified to handle recursive nesting.
        Only purpose is to get the activities from the DCR Graph XML into the data structure
        :return: None
        """
        for events in dcr_xml_root.iter('events'):
            for event in events:
                self.parse_event_or_nest(event)
    
    def parse_initial_marking(self,dcr_xml_root):
        """
        Sets the initial state of the DCR_Graph, which activities are included from the beginning
        """
        for include in dcr_xml_root.iter('included'):
            for event in include:
                event_id = event.get('id')
                node: DCRActivityBase = self.get_event(event_id)
                self.InitialIncluded.add(node)
        for executed_xml in dcr_xml_root.iter('executed'):
            for event in executed_xml:
                event_id = event.get('id')
                node: DCRActivityBase = self.get_event(event_id)
                self.InitialExecuted.add(node)
        for pendingResponse in dcr_xml_root.iter('pendingResponses'):
            for event in pendingResponse:
                event_id = event.get('id')
                node: DCRActivityBase = self.get_event(event_id)
                self.InitialPending.add(node)

    def parse_connections(self,dcr_xml_root):
        """
        Creates all constraints (connections) of a DCR Graph from the XML
        :return: None
        """
        for constraint in dcr_xml_root.iter('constraints'):

            for constraint_type in constraint:

                for connection in constraint_type:

                    connection_source = connection.get('sourceId')

                    connection_destination = connection.get('targetId')

                    source_node = self.get_event(connection_source)
                    target_event = self.get_event(connection_destination)

                    connection_type = DCRConnection.get_connection_type(connection.tag)

                    dcr_connection = None

                    dcr_connection = DCRConnection.create_connection(source_node, target_event, connection_type)

                    self.Connections.add(dcr_connection)

    def get_sub_nodes(self, node):
        """ #own
        Returns a list of all the non-nest sub-nodes of node.
        :param node: The node or node nest for which subnodes are returned.
        :return: A list of DCRActivityBase objects.
        """
        ret = set()
        if node.isNest:
            for n in node.Activities:
                ret.update(self.get_sub_nodes(n))
            return ret            
        else:
            return {node}

    def get_event_by_name(self, activity_name):
        """
        Gets a node by using the
        :param activity_name:
        :return:
        """
        for activity_id, event_name in self.Mappings.items():
            if event_name == activity_name:
                return self.get_event(activity_id)

    def get_event(self, node_id: str) -> DCRActivityBase:
        """
        Returns a certain node, using the activity Id to locate it
        :param node_id:The node id which is located
        :return: A DCRActivityBase object
        """
        for node in self.Nodes:
            if node.ActivityId == node_id:
                return node


    def get_dependees_l(self,nodes):
        """ #own
        Returns all nodes that any node in input nodes depends on.
        :param nodes: The list of nodes for which to get dependees.
        :return: [DRCActivityBase]
        """
        ret = set()
        for node in nodes:
            ret.update(self.get_direct_dependees(node))
        return ret

    #dependee is an agent that is depended on by a depender
    def get_direct_dependees(self,node):
        """ #own
        Returns all nodes that node depends on.
        :param node: The node for which to get dependees.
        :return: [DRCActivityBase]
        """
        # if e' == e
        ret = {node} # every node is a dependee of itself.

        for a in self.get_in_connections(node):
            # if e' ->? e (any relation)
            ret.update(self.get_sub_nodes(a.StartNode)) # There is a connection from e to node
            # We also need to look at the previous relation
            if type(a) in [Condition, Milestone]:
                for a_prev in self.get_in_connections(a.StartNode):
                    # if e' ->+/% e'' ->C/M e
                    if (type(a_prev) in [Include, Exclude] and type(a) in [Condition, Milestone] or
                        # if e' ->R   e'' ->M   e
                        type(a_prev) == Response and type(a) == Milestone):
                        ret.update(self.get_sub_nodes(a_prev.StartNode)) #get_sub_nodes here. Since it's all subnodes.
        return ret

    def get_dependers_l(self,nodes):
        """ #own
        Returns all direct dependencies of all nodes in input nodes.
        :param nodes: The nodes for which to get dependencies.
        :return: [DCRActivityBase]
        """
        ret = set
        for node in nodes:
            ret.update(self.get_direct_dependers(node))
        return ret

    def get_direct_dependers(self,node):
        """ #own
        Returns all direct dependencies of node.
        :param node: The node for which to get dependencies.
        :return: [DCRActivityBase]
        """
        # if e' == e
        ret = {node} # Every node is a direct dependency of itself.

        for a in self.get_out_connections(node):
            # if e' ->? e (any relation)
            ret.update(self.get_sub_nodes(a.EndNode)) # There is a connection from node to e

            # We also need to look at the next relation.
            if type(a) in [Exclude, Include, Response]:
                for a_next in self.get_out_connections(a.EndNode):
                    # if e' ->+/% e'' ->C/M e
                    if (type(a) in [Include, Exclude] and type(a_next) in [Condition, Milestone] or
                        # if e' ->R   e'' ->M   e
                        type(a) == Response and type(a_next) == Milestone):
                        ret.update(self.get_sub_nodes(a_next.EndNode))
        return ret 

    def get_in_connections(self,node:DCRActivityBase, include_ancestors = True,ctypes = []):
        """ #own
        Gets list of incoming connections to node.
        :param node: The node.
        :param include_ancestors: Whether or not to include incoming connections to parent nests. Default is true.
        :param ctypes: Restrict type of connections to look for. Default is None = any type.
        """
        nodes = node.get_ancestors().union({node}) if include_ancestors else {node}
        return {c for c in self.Connections if c.EndNode in nodes and (ctypes == [] or type(c) in ctypes)}

    def get_out_connections(self,node:DCRActivityBase, include_ancestors = True, ctypes = []):
        """ #own
        Gets list of outgoing connections from node.
        :param node: The node.
        :param include_ancestors: Whether or not to include outgoing connections from parent nests. Default is true.
        :param ctypes: Restrict type of connections to look for. Default is None = any type.
        """
        nodes = node.get_ancestors().union({node}) if include_ancestors else {node}
        return {c for c in self.Connections if c.StartNode in nodes and (ctypes == [] or type(c) in ctypes)}

    def collapse(self):
        """ #own
        Collapses nests of activities, if they have only one child, or no connections.
        """

        # It's safe to remove a nest if it has only one child and possibly connections OR if it has no connections and possibly several children.
        # But not if it has connections and more than one child.
        collapsed = set()
        for e in self.Nodes:
            if e.isNest and (len(e.Activities) == 1 or self.get_in_connections(e,False) == set() and self.get_out_connections(e,False) == set()):
                for c in e.Activities:
                    c.Parent = e.Parent
                    if c.Parent is not None:
                        c.Parent.Activities.discard(e)
                        c.Parent.Activities.add(c)

                    # e either has exactly one child, or no connections.
                    for con in self.get_in_connections(e,False):
                        con.EndNode = c
                    for con in self.get_out_connections(e,False):
                        con.StartNode = c
            else:
                collapsed.add(e)
        self.Nodes = collapsed

class DCRInteractionGraph(DCRGraph):
    """ #own
    A DCRGraph that has Users, Services, senders and receivers.
    """
    def __init__(self):
        super().__init__()
        self.Users = set()
        self.Services = set()

    @classmethod
    def from_data(cls, mapping, activities, connections, included, pending, executed, users, services, collapse = True):
        """
        Makes an interaction graph from data.
        :param mapping: The mapping of labels to events.
        :param activities: A list of activities.
        :param connections: A list of connections.
        :param included: Part of the marking. Included events.
        :param pending: Part of the marking. Pending events.
        :param executed: Part of the marking. Executed events.
        :param users: List of roles that are classified as Users.
        :param services: List roles that are classified as Services.
        :param collapse: Whether or not to remove unnecessary nests from actions. Default is True.
        :return: DCRInteractionGraph
        """
        graph = super().from_data(mapping, activities, connections, included, pending, executed)
        
        if collapse:
            graph.collapse()

        graph.set_roles(users, services)

        return graph

    def get_interactions(self, node = None):
        """
        Get all non-nest events of the graph.
        :return: [DCRActivity]
        """
        return {a for a in self.Nodes if not a.isNest} if node is None else self.get_sub_nodes(node)

    def get_roles(self):
        """
        Get all roles of the graph.
        :return: [string]
        """
        return set.union(self.Users,self.Services)

    def get_users(self):
        """
        Get all users of the graph.
        :return: [string]
        """
        return self.Users

    def get_services(self):
        """
        Get all services of the graph.
        :return: [string]
        """
        return self.Services

    def set_roles(self,users,services):
        """
        Set users and services of the graph.
        :param users: [string] a list of roles.
        :param services: [string] a list of roles.
        """
        self.Users = users
        self.Services = services

    # Override to make interaction activities.
    def make_event(self,event_id, event_name):
        """
        Override of DCRGraph make_event to make an interaction event.
        :param event_id: Id of the event.
        :param event_name: Name of the event.
        """
        return DCRInteractionActivity(event_id, event_name)

class DCRChoreography(DCRInteractionGraph):
    """ #own
    Representation of a DCR Choreography.
    A DCRInteractionGraph extended with initiators and receivers, and projections.
    """

    # Override to handle roles correctly.
    def handle_roles(self,node,event):
        """
        Override parsing of roles to include initiator, receiver, user and service.
        All roles must be prefixed with S: ( S for sender/initiator) or R: (R for receiver),
        and optionally also S: (for service) or U: (for user.) Default is service.
        :param node: The node that roles should be added to.
        :param event: The XML-event to be parsed.
        """
        roles = set()
        initiator = None
        receivers = set()
        for role in event.iter('role'):
            if role.text is not None:
                match =  re.match("^(S|R):((U|S):)?([^+]+$)",role.text)
                if match:
                    ms = match.groups()

                    if ms[0] == "S":
                        if initiator is None:
                            initiator = ms[3]
                        else:
                            raise ValueError("Choreography activities must have exactly one initiator.")
                    else: # "R"
                        receivers.add(ms[3])
                    
                    # Add role to Users or Services. Assume Service if no indicator.
                    (self.Users if ms[1] == "U:" else self.Services).add(ms[3])
                    
                    roles.add(ms[3])

                else:
                    raise ValueError("Role "+role.text+" is not well formed.")

        if initiator is None or receivers == set():
            raise ValueError("Choreography activities must have one sender and at least one receiver.")
        node.set_initiator_and_receivers(initiator, receivers)
        node.set_roles(roles)

    def is_projectable(self):
        """
        Determines wheather the choreography instance is projectable for all roles and interactions.
        :return: Bool. True if the choreography is projectable, otherwise false.
        """
        return self.is_projectable_for_actors(self.get_roles(), self.get_interactions())

    # Is projectable for all actors initiating (non-nest) subset of events.
    def is_projectable_delta(self, delta):
        """
        Determines whether the choreography instance is projectable for a set of interactions, and initiators of those interactions.
        :param delta: Set of events for which to determine projectability.
        :return: Bool. True if the choreography is projectable for delta, otherwise false.
        """
        return self.is_projectable_for_actors([e.initiator for e in delta], delta)

    def is_projectable_for_actor(self, actor):
        """
        Determines whether the choreography instance is projectable for an actor, and the events for which that actor is initiator.
        :param actor: Actor for which to determine projectability.
        :return: Bool. True if the choreography is projectable for actor, otherwise false.
        """
        return self.is_projectable_for_actors([actor],[e for e in self.get_interactions() if e.initiator == actor])

    def is_projectable_for_actors(self, actors, delta):
        """
        Determines whether the choreography instance is projectable for a set of actors and a set of events.
        A choreography is projectable if the initiator of an event e is involved, as initiator or receiver, in all events for which there is a direct dependency to e.
        :param actors: Set of actors for which to determine projectability.
        :param delta: Set of events for which to determine projectability.
        :return: Bool. True if the choreography is projectable for delta, otherwise false.
        """
        # make sure that for every interaction, the initiator of an event is present in the previous interaction as either initiator or receiver.
        for action in delta:
            if action.initiator in actors:
                for dp in self.get_direct_dependers(action):
                   if not dp.initiator in action.receivers.union({action.initiator}):
                        print("Warning: The graph is not projectable, as there is a direct dependency from",action.ActivityName,"to",dp.ActivityName, "and",dp.initiator,"not in",action.receivers.union({action.initiator}))
                        return False
        return True

    def project(self):
        """
        Makes end-point projections for all events and actors in the graph.
        :return: [DCRProjection]
        """
        return [self.project_for_actor(a) for a in self.get_roles()]

    def add_event(self,event_set,actor,event):
        """
        Recursively an event to a projection.
        :param event_set: A set of events that have already been added.
        :param actor: The role of the end-point.
        :param event: The event to be added.
        """
        
        activity_id = event.ActivityId

        # If the event has been added already, just return it.
        for e in event_set:
            if activity_id == e.ActivityId:
                return e

        # Else make a new activity.        
        ne = None

        if event.isNest:
            # Nest events are just added as they are.
            ne = DCRActivityNest(activity_id, event.ActivityName, set())
        else:
            initiator = event.initiator
            receivers = event.receivers if initiator == actor else {actor} # receiving action doesn't know other receivers.
            
            ne = DCREndpointActivity(activity_id, event.ActivityName,initiator, receivers,initiator == actor)
            ne.set_datatype(event.datatype)
 
        # If old event has a parent, add or find parent, then add new event as its child.
        if event.Parent is not None:
            parent = self.add_event(event_set,actor, event.Parent)
            parent.add_child_activity(ne)

        ne.set_roles(event.Roles.copy())

        event_set.add(ne)

        return ne

    def get_new_event(self, set, node):
        """
        Get an event that may aldready have been added.
        :param set: The set of new events.
        :param node: The event which may have been added.
        :return: The new node or None if the node has not yet been added.
        """
        return next((e for e in set if e.ActivityId == node.ActivityId), None)


    def project_for_actor(self,actor):
        """
        Make end-point projection for an actor.
        :param actor: The actor for which to make a projection.
        :return: The projection for actor.
        """

        if not self.is_projectable_for_actor(actor):
            raise AssertionError("Choreography is not projecable for "+actor+".")

        # delta is the set of events for which r is the initiator. (And their parent nests.)
        delta = set()
        for e in [e for e in self.get_interactions() if actor == e.initiator]:
                delta.add(e)
                delta.update(e.get_ancestors())
        
        # delta-projection.

        # 1.
        # d AND all e', that any event e in d depends on. e'<e.
        E_d = self.get_dependees_l(delta) 

        # 2.a) Ex intersected with E_d
        Ex_d = {a for a in self.InitialExecuted if a in E_d}
        
        # 2.b) Re intersected with E_d
        Re_d = {a for a in self.InitialPending if a in E_d}

        # 2.c)
        # t = d U (events that have conds or milestones to events in d)
        t = delta.union({e for e in self.Nodes if [c for c in self.get_out_connections(e,ctypes=[Condition, Milestone]) if c.EndNode in delta] != [] })
        # (In intersected with t) U E_d\t
        In_d = (self.InitialIncluded.intersection(t)).union(E_d.difference(t))

        # Now for the connections
        cond_to_d = {c for c in self.Connections if type(c) == Condition and c.EndNode in delta}
        mil_to_d =  {c for c in self.Connections if type(c) == Milestone and c.EndNode in delta}
        resp_to_d = {c for c in self.Connections if type(c) == Response  and c.EndNode in delta}
        cresp_to_d = {c for c in self.Connections if type(c) == CoResponse  and c.EndNode in delta}
        inc_to_d =  {c for c in self.Connections if type(c) == Include   and c.EndNode in delta}
        exc_to_d =  {c for c in self.Connections if type(c) == Exclude   and c.EndNode in delta}

        # 5. Condition relations to events in delta.
        Conds = cond_to_d

        # 6. Milestone relations to events in delta.
        Miles = mil_to_d

        # 7. Response relations to delta and responses to milestones to events in delta.
        # responses to events that have milestones to events in d
        # U
        # (response relations to events in d))
        resp_to_mil_to_d = {c for c in self.Connections if type(c) == Response and c.EndNode in {c.StartNode for c in mil_to_d}}

        Resps = resp_to_d.union(resp_to_mil_to_d)

        cresp_to_mil_to_d = {c for c in self.Connections if type(c) == CoResponse and c.EndNode in {c.StartNode for c in mil_to_d}}
        Cresps = cresp_to_d.union(cresp_to_mil_to_d)

        # 8. Includes.
        #includes to conds to delta U includes to mils to delta U includes to delta
        inc_to_mil_or_cond_to_d = {c for c in self.Connections if type(c) == Include and c.EndNode in {c.StartNode for c in cond_to_d.union(mil_to_d)}}

        Incls = inc_to_d.union(inc_to_mil_or_cond_to_d)

        # 9. Excludes.
        exc_to_mil_or_cond_to_d = {c for c in self.Connections if type(c) == Exclude and c.EndNode in {c.StartNode for c in cond_to_d.union(mil_to_d)}}        

        Excls = exc_to_d.union(exc_to_mil_or_cond_to_d)

        # That was the delta projection. Now on the end-point projection

        # E'
        E_p = {e for e in self.get_interactions() if actor in e.receivers}

        E_d_U_E_p = delta.union(E_p)

        # E'\(E_d\In)
        In_p = E_p.difference(E_d.difference(In_d))

        # M'
        # Same Ex, Re, but In is modified to E'\(E\In)
        
        # Labelling is also extended, but I handle that by making the labelling last.

        # Get list of participants involved.
        users = set()
        services = set()

        # Make the new events.
        activities = set()
        for e in E_d_U_E_p:
            self.add_event(activities, actor, e)

            if not e.isNest:
                (users if e.initiator in self.Users else services).add(e.initiator)
                for r in e.receivers:
                    (users if r in self.Users else services).add(r)

        connections = set()
        for c in Conds.union(Miles).union(Resps).union(Cresps).union(Incls).union(Excls):
            start = self.get_new_event(activities, c.StartNode)
            end   = self.get_new_event(activities, c.EndNode)
            connections.add(DCRConnection.create_connection(start, end, type(c)))

        Executed = {self.get_new_event(activities, e) for e in Ex_d             if e.ActivityId in [e.ActivityId for e in activities]}
        Pending =  {self.get_new_event(activities, e) for e in Re_d             if e.ActivityId in [e.ActivityId for e in activities]}
        Included = {self.get_new_event(activities, e) for e in In_d.union(In_p) if e.ActivityId in [e.ActivityId for e in activities]}

        # 3. and 4.
        mapping = {}        
        for e in activities:
            mapping[e.ActivityId] = e.ActivityName

        # Return the finished projection.
        return DCRProjection().from_data(actor,mapping, activities, connections, Included, Pending, Executed,users,services)



class DCRProjection(DCRInteractionGraph):
    """ #own
    End-point projection.
    Projections are like choreographies, in that they have senders and receivers,
    but you can't make a projection from them.
    """

    @classmethod
    def from_data(cls, actor, mapping, activities, connections, included, pending, executed,users,services,collapse = True):
        """
        Makes a projectioni graph from data.
        :param actor: The actor of the projection.
        :param mapping: The mapping of labels to events.
        :param activities: A list of activities.
        :param connections: A list of connections.
        :param included: Part of the marking. Included events.
        :param pending: Part of the marking. Pending events.
        :param executed: Part of the marking. Executed events.
        :param users: List of roles that are classified as Users.
        :param services: List roles that are classified as Services.
        :param collapse: Whether or not to remove unnecessary nests from actions. Default is True.
        :return: DCRInteractionGraph
        """
        graph = super().from_data(mapping, activities, connections, included, pending, executed,users,services,collapse)
        
        graph.actor = actor

        return graph


    def __init__(self):
        super().__init__()
        self.Users = set()
        self.Services = set()

    def gen_port(self, is_input, from_service, to_service):
        """
        Generate a Jolie communication port.
        :param is_input: Whether the port is an input- or output port.
        :param from_service: Name of the service the port is from.
        :param to_service: Name of the service the port is to.
        :return: String containing the communication port.
        """

        ret = ""
        ret += "\t"+("in" if is_input else "out")+"putPort "+("in"+from_service if is_input else "out"+to_service)+"Service {\n"
        ret += "\t\tlocation: \"socket://localhost:port_of_"+("out" if is_input else "in")+"putPort_'"+("out"+to_service if is_input else "in"+from_service)+"Service'_in_"+(from_service if is_input else to_service)+"\"\n"
        ret += "\t\tprotocol: http { format = \"json\"}\n"
        ret += "\t\tinterfaces: "+self.gen_interface_name(from_service,to_service)+"\n" # FIXME Why is it interfaceS?
        ret += "\t}\n\n"
        return ret

    def gen_service_filename(self,actor,with_path=True):
        """
        Generate the filename of a Service. With or without path and fileextension.
        :param actor: Name of the actor of the service.
        :param with_path: Whether or not to include path and file extension.
        :return: String of the file name.
        """
        ret = actor + "Service"
        return ret if not with_path else "output/"+ret+".ol"

    def gen_interface_filename(self,actor,with_path=True):
        """
        Generate the filename of a set of interfaces. With or without path and fileextension.
        :param actor: Name of the actor of the interfaces.
        :param with_path: Whether or not to include path and file extension.
        :return: String of the file name.
        """
        ret = actor+"Interfaces"
        return ret if not with_path else "output/"+ret+".iol"

    def gen_interface_name(self,from_actor,to_actor):
        """
        Generate the name of an interface.
        :param from_actor: The actor that invokes the interface.
        :param to_actor: The actor of the interface that is invoked.
        :return: String of the interface name.
        """
        return from_actor+to_actor+"Interface"

    def gen_interfaces(self,operations, is_in):
        """
        Generate an interfaces.
        :param operations: The operations/actions to include in the interface.
        :param is_in: Whether the interface is for this service, or for invoking operations of another.
        :return: String of the interface.
        """
        ret = ""
        for event_actor,events in operations.items():
            if is_in:
                interface_name = self.gen_interface_name(event_actor,self.actor)
            else:
                interface_name = self.gen_interface_name(self.actor,event_actor)

            ret += "interface "+interface_name+"{\n\toneWay:\n\t\t"
            ret += ",\n\t\t".join([self.gen_operation(e) for e in events])
            ret += "\n}\n\n"
        return ret

    def write_file(self,fname, fcontents):
        if os.path.exists(fname):
            os.remove(fname)
        f = open(fname, "x")
        f.write(fcontents)
        f.close()

    def convert_datatype(self,e):
        """
        Convert DCR data type to Jolie data type.
        :param e: The event.
        :return: String of the converted datatype.
        """
        datatype = 'CUSTOM'
        if e.datatype:
            if e.datatype == 'text':
                datatype = 'string'
            elif e.datatype == 'float':
                datatype = 'double'
            elif e.datatype in ['void', 'bool', 'int', 'long', 'raw', 'any']:
                datatype = e.datatype
        else:
            datatype = 'void'

        return datatype

    def gen_operation(self,e):
        """
        Generate an operation-string for an interface with name and datatype.
        :param e: The event.
        :return: String of the interface operation.
        """
        return e.ActivityName.lower().replace(' ','_')+"("+self.convert_datatype(e)+")"

    def generate_jolie(self,output_folder_path):
        """
        Generate a Jolie template from the projection.
        :param output_folder_path: raise NotImplementedError()
        """

        in_interfaces = defaultdict(set)
        out_interfaces = defaultdict(set)

        inputports = set()
        outputports = set()

        for e in self.get_interactions():
            if self.actor == e.initiator:
                outputports.update(e.receivers)
                for r in e.receivers:
                    out_interfaces[r].add(e)
            else: # We know by def sth that actor is the receiver.
                inputports.add(e.initiator)
                in_interfaces[e.initiator].add(e)

        interface_str = self.gen_interfaces(in_interfaces,True)
        interface_str += self.gen_interfaces(out_interfaces,False)

        self.write_file(self.gen_interface_filename(self.actor),interface_str)

        service_str = 'include "' + self.gen_interface_filename(self.actor,False) + '.iol"'

        service_str += "\n\nservice "+ self.actor+"Service{\n\texecution: {"+ ("single" if self.actor in self.Users else "sequential") + "}\n\n"

        for n in inputports:
            service_str += self.gen_port(True,n,self.actor)

        for n in outputports:
            service_str += self.gen_port(False,self.actor,n)

        service_str += "\n\tmain {\n\n\t}\n}"
        
        self.write_file(self.gen_service_filename(self.actor),service_str)

        return