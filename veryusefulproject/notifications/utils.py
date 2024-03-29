from django.contrib.auth import get_user_model

from veryusefulproject.orders.models import Order, OrderIntermediaryCandidate


MODEL_MAP = {}

USER_MODEL_MAP = {
    'User': get_user_model(),
}

ORDER_MODEL_MAP = {
    'Order': Order,
    'OrderIntermediaryCandidate': OrderIntermediaryCandidate,
}

MODEL_MAP.update(USER_MODEL_MAP)
MODEL_MAP.update(ORDER_MODEL_MAP)


MODEL_UNIQUE_IDENTIFIER_FIELD_MAP = {
    "Order": "url_id",
    "User": "username",
}


def return_affected_entities_unique_identifiers(notification):
    """
    Returns a list of unique identifiers of the affected entities of a notification.
    """

    result = []
    affected_entities = notification.notification_object.notificationobjectaffectedentity_set.all()

    for affected_entity in affected_entities:
        field = MODEL_UNIQUE_IDENTIFIER_FIELD_MAP[affected_entity.entity_type.entity_name]
        affected = MODEL_MAP[affected_entity.entity_type.entity_name].objects.get(
            id=affected_entity.entity_id
        )
        affected_identity_unique_identifier = getattr(affected, field)
        result.append(affected_identity_unique_identifier)

    return result


def check_placeholder_substring(placeholder_substring):
    """
    Returns a tuple of the role, name, and field of the model that the placeholder 
    substring will be replaced with.
    """

    if placeholder_substring.count(":") != 2:
        raise Exception("Invalid placeholder substring.")

    role = placeholder_substring[1:placeholder_substring.find(":")]
    name = placeholder_substring[
        placeholder_substring.find(":") + 1:placeholder_substring.rfind(":")]
    field = placeholder_substring[placeholder_substring.rfind(":") + 1:-1]

    if not role in ["actor", "affected", "involved"]:
        raise Exception("Invalid placeholder substring.")

    if len(name) == 0 or len(field) == 0:
        raise Exception("Invalid placeholder substring.")

    return role, name, field
    

def parse_action_string(action_string):
    """
    Returns a list of dictionaries, where each dictionary contains the role, name,
    and field of the model that the placeholder substring will be replaced with.
    """

    temp_action_string_parsed_result = {"indexes": []}
    list_to_return = []

    for index, character in enumerate(action_string):
        if character == '{':
            temp_action_string_parsed_result["indexes"].append(index)
        elif character == '}':
            temp_action_string_parsed_result["indexes"].append(index)
            role, name, field = check_placeholder_substring(
                action_string[
                    temp_action_string_parsed_result["indexes"][0]:temp_action_string_parsed_result["indexes"][1] + 1
                ]
            )
            temp_action_string_parsed_result["role"] = role
            temp_action_string_parsed_result["name"] = name
            temp_action_string_parsed_result["field"] = field
            temp_action_string_parsed_result.pop("indexes")
            list_to_return.append(temp_action_string_parsed_result)
            temp_action_string_parsed_result = {"indexes": []}

    return list_to_return


def stringify_notification(notification_object):
    """
    Returns a string representation of a notification.

    How does it work?
    1. Fetch the action object of a notification.
    2. Parse the "action" property of the action object by identifying all the 
    placeholder substrings (strings that start and end with curly braces) and seeing
    what models need to be queried, in order to compose a string representation of the 
    notification.
    3. Query the necessary models, and compose the string representation.
    4. Return the string representation.
    """
    
    replacement_strings = []

    actor_count = 0
    affected_count = 0
    involved_count = 0

    actor = notification_object.notificationobjectactor_set.all()
    affected = notification_object.notificationobjectaffectedentity_set.all()
    involved = notification_object.notificationobjectinvolvedentity_set.all()

    action_string = notification_object.action.action
    action_string_parsed_result = parse_action_string(action_string)
    for item in action_string_parsed_result:
        if item["role"] == "actor":
            actor = MODEL_MAP[item["name"]].objects.get(id=actor[actor_count].entity_id)
            value_for_replacement = getattr(actor, item["field"])
            replacement_strings.append(str(value_for_replacement))
            actor_count += 1

        elif item["role"] == "affected":
            affected = MODEL_MAP[item["name"]].objects.get(id=affected[affected_count].entity_id)
            value_for_replacement = getattr(affected, item["field"])
            replacement_strings.append(str(value_for_replacement))
            affected_count += 1

        elif item["role"] == "involved":
            involved = MODEL_MAP[item["name"]].objects.get(id=involved[involved_count].entity_id)
            value_for_replacement = getattr(involved, item["field"])
            replacement_strings.append(str(value_for_replacement))
            involved_count += 1
        else:
            raise Exception("Invalid role.")
    
    while action_string.find("{") != -1:
        action_string = action_string.replace(
            action_string[
                action_string.find("{"):action_string.find("}") + 1
            ],
            replacement_strings.pop(0)
        )
   
    return action_string
