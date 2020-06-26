QUERY_REQUIREMENTS = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
prefix xml: <http://www.w3.org/XML/1998/namespace/>
prefix mms-ontology: <https://opencae.jpl.nasa.gov/mms/rdf/ontology/>
prefix mms-graph: <https://opencae.jpl.nasa.gov/mms/rdf/graph/>
prefix mms-property: <https://opencae.jpl.nasa.gov/mms/rdf/property/>
prefix mms-class: <https://opencae.jpl.nasa.gov/mms/rdf/class/>
prefix mms-element: <https://opencae.jpl.nasa.gov/mms/rdf/element/>
prefix mms-artifact: <https://opencae.jpl.nasa.gov/mms/rdf/artifact/>
prefix mms-index: <https://opencae.jpl.nasa.gov/mms/rdf/index/>
prefix xmi: <http://www.omg.org/spec/XMI/20131001#>
prefix uml: <http://www.omg.org/spec/UML/20161101#>
prefix uml-model: <https://www.omg.org/spec/UML/20161101/UML.xmi#>
prefix uml-primitives: <https://www.omg.org/spec/UML/20161101/PrimitiveTypes.xmi#>
prefix uml-class: <https://opencae.jpl.nasa.gov/mms/rdf/uml-class/>
prefix uml-property: <https://opencae.jpl.nasa.gov/mms/rdf/uml-property/>

# `Class` that has an `appliedStereotypeInstance` `InstanceSpecification` whose type is <<Requirement>> Stereotype (ID)
select ?instance ?slot ?valueString from mms-graph:data.tmt {
    # `Class` that has an `appliedStereotypeInstance`...
    ?class a uml-class:Class ;
        mms-property:appliedStereotypeInstance ?instance ;
        .

    # `InstanceSpecification` Stereotype classifier and all slots
    ?instance mms-property:classifierFromInstanceSpecification ?stereotype ;
        mms-property:slot ?slot ;
        .

    # stereotype
    ?stereotype a uml-class:Stereotype ;
        .

    # Slot --> value, and defining feature
    ?slot mms-property:valueValueSpecificationFromSlot ?slotValue ;
        mms-property:definingFeatureStructuralFeature ?feature ;
        .

    # defining feature's name
    ?feature mms-property:nameString ?featureName ;
        .

    # value --> string
    ?slotValue a uml-class:LiteralString ;
        mms-property:valueString ?valueString ;
        .

    # defining feature(s) name(s)
    values ?featureName {
        "Text"
    }
}
"""


QUERY_ELEMENTS = """prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#>
prefix owl: <http://www.w3.org/2002/07/owl#>
prefix xsd: <http://www.w3.org/2001/XMLSchema#>
prefix xml: <http://www.w3.org/XML/1998/namespace/>
prefix mms-ontology: <https://opencae.jpl.nasa.gov/mms/rdf/ontology/>
prefix mms-graph: <https://opencae.jpl.nasa.gov/mms/rdf/graph/>
prefix mms-property: <https://opencae.jpl.nasa.gov/mms/rdf/property/>
prefix mms-class: <https://opencae.jpl.nasa.gov/mms/rdf/class/>
prefix mms-element: <https://opencae.jpl.nasa.gov/mms/rdf/element/>
prefix mms-artifact: <https://opencae.jpl.nasa.gov/mms/rdf/artifact/>
prefix mms-index: <https://opencae.jpl.nasa.gov/mms/rdf/index/>
prefix xmi: <http://www.omg.org/spec/XMI/20131001#>
prefix uml: <http://www.omg.org/spec/UML/20161101#>
prefix uml-model: <https://www.omg.org/spec/UML/20161101/UML.xmi#>
prefix uml-primitives: <https://www.omg.org/spec/UML/20161101/PrimitiveTypes.xmi#>
prefix uml-class: <https://opencae.jpl.nasa.gov/mms/rdf/uml-class/>
prefix uml-property: <https://opencae.jpl.nasa.gov/mms/rdf/uml-property/>

select * from mms-graph:data.tmt {
    ?element a/rdfs:subClassOf* uml-class:Class
    {
        ?element rdfs:label ?label 
    } union {
        ?element mms-property:name ?label
    }
    
    filter(isLiteral(?label) && ?label != "")
}
"""


INSERT_BLOCKS = """
mms-autocref-i:Evaluation.{evaluation_uuid} a mms-autocref:Evaluation ;
    mms-autocref:evaluates <{input_uri}> ;
    mms-autocref:inputText \"\"\"{input_text}\"\"\" ;
    mms-autocref:outputText \"\"\"{output_text}\"\"\" ;
    mms-autocref:reference mms-autocref-i:Reference.{reference_uuid} ;
    .

mms-autocref-i:Reference.{reference_uuid}
  a mms-autocref:Reference ;
  mms-autocref:token mms-autocref-i:Token.{reference_uuid} ;
  mms-autocref:match <{match_uri}> ;
  .

mms-autocref-i:Token.{reference_uuid}
  a mms-autocref:Token ;
  mms-autocref:tokenStart "{token_position}"^^xsd:integer ;
  mms-autocref:tokenText \"\"\"{token_text}\"\"\" ;
  .
"""


INSERT_QUERY = """
prefix mms-autocref: <https://opencae.jpl.nasa.gov/mms/rdf/autocref/>
prefix mms-autocref-i: <https://opencae.jpl.nasa.gov/mms/rdf/autocref-instance/>

insert data {{
  graph <https://opencae.jpl.nasa.gov/mms/rdf/graph/autocref.tmt.test> {{
    {insert_blocks}
  }}
}}
"""