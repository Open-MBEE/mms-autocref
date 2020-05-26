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


class ElementWithOSMCLink(object):
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
        'element_id': 'str',
        'osmc_link': 'str'
    }

    attribute_map = {
        'element_id': 'elementId',
        'osmc_link': 'osmcLink'
    }

    def __init__(self, element_id=None, osmc_link=None):  # noqa: E501
        """ElementWithOSMCLink - a model defined in OpenAPI"""  # noqa: E501

        self._element_id = None
        self._osmc_link = None
        self.discriminator = None

        self.element_id = element_id
        self.osmc_link = osmc_link

    @property
    def element_id(self):
        """Gets the element_id of this ElementWithOSMCLink.  # noqa: E501


        :return: The element_id of this ElementWithOSMCLink.  # noqa: E501
        :rtype: str
        """
        return self._element_id

    @element_id.setter
    def element_id(self, element_id):
        """Sets the element_id of this ElementWithOSMCLink.


        :param element_id: The element_id of this ElementWithOSMCLink.  # noqa: E501
        :type: str
        """
        if element_id is None:
            raise ValueError("Invalid value for `element_id`, must not be `None`")  # noqa: E501

        self._element_id = element_id

    @property
    def osmc_link(self):
        """Gets the osmc_link of this ElementWithOSMCLink.  # noqa: E501


        :return: The osmc_link of this ElementWithOSMCLink.  # noqa: E501
        :rtype: str
        """
        return self._osmc_link

    @osmc_link.setter
    def osmc_link(self, osmc_link):
        """Sets the osmc_link of this ElementWithOSMCLink.


        :param osmc_link: The osmc_link of this ElementWithOSMCLink.  # noqa: E501
        :type: str
        """
        if osmc_link is None:
            raise ValueError("Invalid value for `osmc_link`, must not be `None`")  # noqa: E501

        self._osmc_link = osmc_link

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
        if not isinstance(other, ElementWithOSMCLink):
            return False

        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        """Returns true if both objects are not equal"""
        return not self == other
