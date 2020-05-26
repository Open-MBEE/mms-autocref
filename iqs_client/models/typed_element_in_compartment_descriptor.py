# coding: utf-8

"""
    IncQuery Server

    No description provided (generated by Openapi Generator https://github.com/openapitools/openapi-generator)  # noqa: E501

    OpenAPI spec version: 0.12.0
    Generated by: https://openapi-generator.tech
"""


import pprint
import re  # noqa: F401

import six


class TypedElementInCompartmentDescriptor(object):
    """NOTE: This class is auto generated by OpenAPI Generator.
    Ref: https://openapi-generator.tech

    Do not edit the class manually.
    """

    """
    Attributes:
      openapi_types (dict): The key is attribute name
                            and the value is attribute type.
      attribute_map (dict): The key is attribute name
                            and the value is json key in definition.
    """
    openapi_types = {
        'element': 'ElementInCompartmentDescriptor',
        'type': 'str',
        'name': 'str'
    }

    attribute_map = {
        'element': 'element',
        'type': 'type',
        'name': 'name'
    }

    def __init__(self, element=None, type=None, name=None):  # noqa: E501
        """TypedElementInCompartmentDescriptor - a model defined in OpenAPI"""  # noqa: E501

        self._element = None
        self._type = None
        self._name = None
        self.discriminator = None

        self.element = element
        self.type = type
        self.name = name

    @property
    def element(self):
        """Gets the element of this TypedElementInCompartmentDescriptor.  # noqa: E501


        :return: The element of this TypedElementInCompartmentDescriptor.  # noqa: E501
        :rtype: ElementInCompartmentDescriptor
        """
        return self._element

    @element.setter
    def element(self, element):
        """Sets the element of this TypedElementInCompartmentDescriptor.


        :param element: The element of this TypedElementInCompartmentDescriptor.  # noqa: E501
        :type: ElementInCompartmentDescriptor
        """
        if element is None:
            raise ValueError("Invalid value for `element`, must not be `None`")  # noqa: E501

        self._element = element

    @property
    def type(self):
        """Gets the type of this TypedElementInCompartmentDescriptor.  # noqa: E501


        :return: The type of this TypedElementInCompartmentDescriptor.  # noqa: E501
        :rtype: str
        """
        return self._type

    @type.setter
    def type(self, type):
        """Sets the type of this TypedElementInCompartmentDescriptor.


        :param type: The type of this TypedElementInCompartmentDescriptor.  # noqa: E501
        :type: str
        """
        if type is None:
            raise ValueError("Invalid value for `type`, must not be `None`")  # noqa: E501

        self._type = type

    @property
    def name(self):
        """Gets the name of this TypedElementInCompartmentDescriptor.  # noqa: E501


        :return: The name of this TypedElementInCompartmentDescriptor.  # noqa: E501
        :rtype: str
        """
        return self._name

    @name.setter
    def name(self, name):
        """Sets the name of this TypedElementInCompartmentDescriptor.


        :param name: The name of this TypedElementInCompartmentDescriptor.  # noqa: E501
        :type: str
        """
        if name is None:
            raise ValueError("Invalid value for `name`, must not be `None`")  # noqa: E501

        self._name = name

    def to_dict(self):
        """Returns the model properties as a dict"""
        result = {}

        for attr, _ in six.iteritems(self.openapi_types):
            value = getattr(self, attr)
            if isinstance(value, list):
                result[attr] = list(map(
                    lambda x: x.to_dict() if hasattr(x, "to_dict") else x,
                    value
                ))
            elif hasattr(value, "to_dict"):
                result[attr] = value.to_dict()
            elif isinstance(value, dict):
                result[attr] = dict(map(
                    lambda item: (item[0], item[1].to_dict())
                    if hasattr(item[1], "to_dict") else item,
                    value.items()
                ))
            else:
                result[attr] = value

        return result

    def to_str(self):
        """Returns the string representation of the model"""
        return pprint.pformat(self.to_dict())

    def __repr__(self):
        """For `print` and `pprint`"""
        return self.to_str()

    def __eq__(self, other):
        """Returns true if both objects are equal"""
        if not isinstance(other, TypedElementInCompartmentDescriptor):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
