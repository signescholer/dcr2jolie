# coding=utf-8
"""The module contains all classes for the representations of DCR relations"""
from abc import ABC, abstractmethod
from enum import Enum, auto
import string

"""
Condition: creates a relation between an activity A and
an activity B such that B can only occur if first A has occurred

Response: The Response connection creates a relation between an activity A and an activity B such that B has to
occur, at least once, at some point after, if A occurs. B can occur even if A never occurs. But if A, then B.

Include: creates a relation between an activity A and an activity B such that the occurrence of activity A
makes possible the occurrence of activity B if it wasn't previously included in the workflow

Exclude: creates a relation between an activity A and an activity B such that B cannot occur
if first A has occurred.

Milestone: creates a relation between an activity A and an activity B such that B can occur initially.
But if A becomes pending for a response connection by another activity C, then B cannot occur
until A has occurred

Spawn: The Spawn connection creates a relation between an activity A and a sub-activity B such that,
when A occurs, a new instance of B is created
"""

class DCRConnection(ABC):
    """ # modified, added methods.
    Abstract class for DCR relations to be inherited
    """

    def __str__(self):
        return self.StartNode.str_name() + "-" + DCRConnection.get_connection_string(type(self)) + "-" + self.EndNode.str_name()

    def __init__(self, start_node, end_node):
        self.StartNode = start_node
        self.EndNode = end_node
        self.Expression = None
        self.HasExpression = False

    @staticmethod
    def get_connection_type(connection_type:string):
        """ # own
        Get the connection type from a string.
        :param connetion_type: string.
        :return: Type of connection matching the string.
        """
        if connection_type == "condition":
            return Condition
        elif connection_type == "response":
            return Response
        elif connection_type == "exclude":
            return Exclude
        elif connection_type == "include":
            return Include
        elif connection_type == "milestone":
            return Milestone
        elif connection_type == "coresponse":
            return CoResponse
        else:
            raise ValueError('Could not recognize connection_type ' + connection_type)
    
    @staticmethod
    def get_connection_string(connection_type: type):
        """ # own
        Get a string of a connection type from a connection type.
        :param connection_type: Type for which to get a string.
        :return: string of the type.
        """
        if connection_type == Condition:
            return "condition"
        elif connection_type == Response:
            return "response"
        elif connection_type == Exclude:
            return "exclude"
        elif connection_type == Include:
            return "include"
        elif connection_type == Milestone:
            return "milestone"
        elif connection_type == CoResponse:
            return "coresponse"
        else:
            raise ValueError('Could not recognize connection_type ' + connection_type)
    

    @staticmethod
    def create_connection(start_node, end_node, connection_type: type, expression=None):
        """
        Static method that builds a certain connection based on the enum connection type
        :param expression: If expression exists default is no expression
        :param start_node: The origin node of the connection
        :param end_node: destination node of the connection
        :param connection_type: the type of constraint related to the connection
        :return: Instance of the constraint
        """
        connection = None
        if connection_type == Condition:
            connection = Condition(start_node, end_node)
        elif connection_type == Response:
            connection = Response(start_node, end_node)
        elif connection_type == Exclude:
            connection = Exclude(start_node, end_node)
        elif connection_type == Include:
            connection = Include(start_node, end_node)
        elif connection_type == Milestone:
            connection = Milestone(start_node, end_node)
        elif connection_type == CoResponse:
            connection = CoResponse(start_node, end_node)
        if connection is not None:

            # if the connection is not None it is returned otherwise an Error is raised
            if expression is None:
                return connection
            else:
                connection.add_expression(expression)
                return connection
        else:
            raise ValueError('connection was None')

    @abstractmethod
    def perform_transition(self, marking):
        """
        Distributor for the performance of marking transition
        :param marking:
        :return: True if conformant, False if not
        """
        pass

    def add_expression(self, expression):
        """
        Add an expression to the connection
        :param expression: The expression that was parsed from the Graph XML
        """
        self.Expression = expression
        self.HasExpression = True


class Include(DCRConnection):
    """
    The representation of an Include relations
    :DCRConnection implementer
    """

    def __init__(self, start_node, end_node):
        """
        Constructor for an Include connection
        :super DCRConnection
        :param start_node
        :param end_node
        :see also DCRConneciton
        """
        super().__init__(start_node, end_node)

    def perform_transition(self, marking):
        """
        Includes the target activities
        :param marking: Needed to manipulate the marking
        :return:
        """
        if self.EndNode not in marking.Included:
            marking.Included.append(self.EndNode)
        if hasattr(self.EndNode, "Activities"):
            for activity in self.EndNode.Activities:
                if activity not in marking.Included:
                    marking.Included.append(activity)
        elif self.EndNode.NestingActivity is not None:
            if self.EndNode.NestingActivity is not marking.Included:
                marking.Included.append(self.EndNode.NestingActivity)


class Milestone(DCRConnection):
    """
    The class that represents a Milestone relation
    """

    def __init__(self, start_node, end_node):
        """
        Constructor for the Milestone
        :param start_node:
        :param end_node:
        """
        super().__init__(start_node, end_node)
        #self.EndNode.set_is_milestone_target()

    def perform_transition(self, marking):
        """
        Empty method stub for Milestone and Condition
        :param marking:
        :return:
        """
        pass


class Condition(DCRConnection):
    """
    The class that represents a condition relation
    """

    def __init__(self, start_node, end_node):
        super().__init__(start_node, end_node)
        #self.EndNode.set_is_condition_target()

    def perform_transition(self, marking):
        """
        Empty method stub in condition and milestone
        :param marking:
        :return:
        """
        pass


class Exclude(DCRConnection):
    """
    The class represents the Exclude relation
    """

    def __init__(self, start_node, end_node):
        super().__init__(start_node, end_node)

    def perform_transition(self, marking):
        """
          Override for base method
          :param marking: Base-Marking on which the transition is checked
          :return: True if conformant, False if not
          """
        if self.EndNode in marking.Included:
            marking.Included.remove(self.EndNode)
        if hasattr(self.EndNode, "Activities"):
            for activity in self.EndNode.Activities:
                if activity in marking.Included:
                    marking.Included.remove(activity)
        elif self.EndNode.NestingActivity is not None:
            if not any(activity in marking.Included for activity in self.EndNode.NestingActivity.Activities):
                marking.Included.remove(self.EndNode.NestingActivity)


class Response(DCRConnection):
    """
    The class represents a Response connection in a DCR graph
    """

    def __init__(self, start_node, end_node):
        """
        Constructor for Response, calls super __init__
        :param start_node:
        :param end_node:
        """
        super().__init__(start_node, end_node)

    def perform_transition(self, marking):
        """
        Performs the transition for a response connection
        :param marking:
        :return:
        """
        if self.EndNode not in marking.PendingResponse:
            marking.PendingResponse.append(self.EndNode)

        if hasattr(self.EndNode, "Activities"):
            for activity in self.EndNode.Activities:
                if activity not in marking.PendingResponse:
                    marking.PendingResponse.append(activity)
        elif self.EndNode.NestingActivity is not None:
            # if any(activity in self.EndNode.NestingActivity.Activities for activity in marking.PendingResponse):
            if self.EndNode.NestingActivity not in marking.PendingResponse:
                marking.PendingResponse.append(self.EndNode.NestingActivity)

class CoResponse(DCRConnection):
    """ #own
    The class represents a CoResponse connection in a DCR graph
    """

    def __init__(self, start_node, end_node):
        """
        Constructor for CoResponse, calls super __init__
        :param start_node:
        :param end_node:
        """
        super().__init__(start_node, end_node)

    def perform_transition(self, marking):
        """
        Performs the transition for a coresponse connection
        :param marking:
        :return:
        """
        if self.EndNode in marking.PendingResponse:
            marking.PendingResponse.remove(self.EndNode)

        # FIXME This should be changed completely.
        # It doesn't take recursive nesting into account,
        # and it doesn't handle groups correctly.
        if hasattr(self.EndNode, "Activities"):
            for activity in self.EndNode.Activities:
                if activity in marking.PendingResponse:
                    marking.PendingResponse.remove(activity)
        
        elif self.EndNode.NestingActivity is not None:
            if any(activity in self.EndNode.NestingActivity.Activities for activity in marking.PendingResponse):
                if self.EndNode.NestingActivity not in marking.PendingResponse:
                    marking.PendingResponse.append(self.EndNode.NestingActivity)