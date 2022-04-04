# coding=utf-8
""" Contains all DCR activity classes and their definitions"""

from abc import ABC
from ssl import ALERT_DESCRIPTION_BAD_CERTIFICATE_STATUS_RESPONSE

class DCRActivityBase(ABC):
    """ # modified, added methods and datatypes, recursive nesting...
    The base class for all DCR activities
    """

    def str_name(self):
        """ #own """
        return self.ActivityName

    def __init__(self, activity_id=str, activity_name=str):
        """
        The constructor of the abstracted super class DCRActivityBase that defines how attributes
        have to look like
        :param activity_id: The activity id
        :param activity_name: The name of the activity
        :param attributes: attributes that
        """
        if activity_id is None or activity_name is None:
            raise TypeError('Parameters may not be null')

        self.ActivityId = activity_id
        self.ActivityName = activity_name
        self.Roles = set()
        self.Parent = None

        #own
        self.isNest = False

    def set_roles(self, roles: list):
        """
        Sets the roles for the activity
        :param roles: roles that are set for the activity
        """
        for role in roles:
            self.Roles.add(role)

    #own moved this from DCRActivity, for recursive nesting.
    def set_parent_activity(self, parent):
        """
        Set the parent nesting activity that contains this activity
        :param parent: DCRActivityNest
        """
        self.Parent = parent

    def get_ancestors(self):
        """ #own
        Get parent nests, parents of parents aso.
        """
        if self.Parent is None:
            return set()
        else:
            return self.Parent.get_ancestors().union({self.Parent})

    def get_successors(self):
        """ #own
        Get child nodes, children of children aso.
        """
        if not self.isNest:
            return set()
        else:
            children = self.Activities # Allowed, because we know it's a nest.
            for child in children:
                children.update(child.get_successors())
            return children

class DCRActivity(DCRActivityBase):
    """ #modified, added data type
    A default DCRActivity
    """

    def __init__(self, activity_id, activity_name):
        """
        This method constructs an activity based on certain events. Subclass of DCRActivityBase
        :param activity_id: The id of the event tag
        :param activity_name: the activity name of the mappings tag in the xml
        """
        super().__init__(activity_id, activity_name)

        #own
        self.datatype = None

    def set_datatype(self,datatype):
        """ #own
        Set the data type of the activity
        :param datatype: The data type.
        """
        self.datatype = datatype

class DCRInteractionActivity(DCRActivity):
    """ #own
    An InteractionActivity that has an initiator and one or more receivers.
    """

    def __init__(self, activity_id=str, activity_name=str, initiator = None, receivers = None):

        super().__init__(activity_id, activity_name)

        self.receivers = receivers
        self.initiator = initiator

    def set_initiator_and_receivers(self, initiator, receivers: []):
        """
        Sets the initiator and receiver(s) of the activity.
        :param initiator: The initiator
        :param receivers: The receiver(s)
        """
        self.initiator = initiator
        self.receivers = receivers

    def get_initiator_and_receivers(self):
        return self.senders.union({self.initiator})

class DCREndpointActivity(DCRInteractionActivity):
    """ #own
    An End-point activity, that has initiator and receiver and is either input or output.
    """

    def __init__(self,activity_id, activity_name, initiator, receivers, is_output):
        super().__init__(activity_id,activity_name,initiator,receivers)

        self.is_output = is_output

    # override
    def str_name(self):
        activity_name = self.ActivityName

        if not self.isNest:
            receiver_str = "{" +','.join(self.receivers)+"}" if len(self.receivers) > 1 else next(iter(self.receivers)) #hack to get element without removing it.
            activity_name = ("!" if self.is_output else "?")+"("+self.ActivityName+', '+self.initiator+"->" + receiver_str+")"

        return activity_name

class DCRActivityNest(DCRActivityBase):
    """ # own
    Representation of Nesting activity of DCR graphs
    """

    def __init__(self, activity_id=str, activity_name=str, activities=None):
        """
        Constructor for a nesting activity
        :param activity_id: The id of the event tag
        :param activity_name: the activity name of the mappings tag in the xml
        :param activities: Contains all activities that are nested under the nesting activity
        """

        super().__init__(activity_id, activity_name)

        activities = activities

        if activities is None:
            activities = set()
        else:
            for activity in activities:
                activity.set_parent_activity(self)
 
        self.isNest = True

        self.Activities = activities
        # Set self as Parent in all activities.

    def add_child_activity(self, activity):
        activity.set_parent_activity(self)
        self.Activities.add(activity)
