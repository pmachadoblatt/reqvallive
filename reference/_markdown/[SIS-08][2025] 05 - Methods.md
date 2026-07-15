---
source: [SIS-08][2025] 05 - Methods.pdf
converted: 2026-07-14T22:20:55Z
---

IEA-P – DEPARTAMENTO DE PROJETOS
(PROJECT DEPARTMENT)
Means of Compliance and Success
Criteria
[2025]
Prof. Dr. Christopher S. Cerqueira

https://www.youtube.com/watch?v=MpaHR-V_R-o

3

4

relações
SYSTEM OF
INTEREST
CONOPS Level Test Article
REQUIREMENTS V&V Method Stage
Model
Test
Enabling
Baseline
Systems
Facility
Plans
Procedure
Documentation Execution
5

| Validation x Verification |     |     |     |     |     |     |
| ------------------------- | --- | --- | --- | --- | --- | --- |
• VERIFYING  A  SYSTEM:  • VALIDATING  A  SYSTEM:  Building  the
Building  the  system  right  system:  making  sure  that  the
right:  ensuring  that  the  system does what it is supposed to do in
system  complies  with  its  intended  environment.  Validation
| the  | system  | determines  | the  | correctness  |     | and  |
| ---- | ------- | ----------- | ---- | ------------ | --- | ---- |
X
| requirements  | and  | completeness  | of  the  | end  | product  | and  |
| ------------- | ---- | ------------- | -------- | ---- | -------- | ---- |
conforms to its design. ensures  that  the  system  will  satisfy  the
actual needs of the stakeholders.

Questions:
HOW
• What are the products • When to implement
and requirements by applying the
• How to verify them by
subject of the chosen verification
considering the
verification process? strategy?
methods stated in the
technical specification
and the System level?
WHAT WHEN

| Verification | & Validation | Methods |
| ------------ | ------------ | ------- |
“HOW”

How would you guarantee a system
is working?
10

V&V Requirements Development
• V&V requirements should be developed concurrently with system
requirements
• Systems Engineer (SE) works with Requirement Owners to help establish
methodology
- On small projects, SE may try at method, phase, level, then
have discipline experts' review.
- Larger projects, may use V&V Working Group or
a series of sessions with Stakeholders.
SE should ensure all requirements are verifiable as written
11

Analysis
• The use of mathematical modeling and • The use of mathematical modeling and
predict the predict the
analytical techniques to analytical techniques to
suitability suitability
of a design to stakeholder of a design to stakeholder
expectations based on calculated data or expectations based on calculated data or
data derived from lower system structure data derived from lower system structure
end product verifications. end product verifications.
• Analysis is generally used when a • Analysis is generally used when a
prototype; engineering model; or prototype; engineering model; or
fabricated, assembled, and integrated fabricated, assembled, and integrated
product is not available. Analysis includes product is not available. Analysis includes
the use of modeling and simulation as the use of modeling and simulation as
analytical tools. A model is a analytical tools. A model is a
mathematical representation of reality. A mathematical representation of reality. A
simulation is the manipulation of a simulation is the manipulation of a
model. Analysis can include verification model.
by similarity of a heritage product.

Demonstration
• Showing that the use of an end product • Showing that the use of an end product
achieves the individual specified stakeholder
achieves the
requirement expectations as defined in the
.
NGOs and the ConOps
.
• It is generally a basic confirmation of
performance capability, differentiated from
• It is generally a basic confirmation of
testing by the lack of detailed data gathering.
behavioral capability, differentiated from
Demonstrations can involve the use of
testing by the lack of detailed data gathering.
physical models or mock-ups; for example, a
Demonstrations can involve the use of
requirement that all controls shall be
physical models or mock-ups; for example,
reachable by the pilot could be verified by
an expectation that controls are readable by
having a pilot perform flight-related tasks in
the pilot in low light conditions could be
a cockpit mock-up or simulator. A
validated by having a pilot perform flight-
demonstration could also be the actual
related tasks in a cockpit mock-up or
operation of the end product by highly
simulator under those conditions.
qualified personnel, such as test pilots, who
perform a one-time event that demonstrates
a capability to operate at extreme limits of
system performance, an operation not
normally expected from a representative
operational pilot.

Inspection
• The visual examination of a realized end • The visual examination of a realized end
product. product.
verify • Inspection is generally used to
• Inspection is generally used to
validate the presence of a
physical design features or
physical design features or
specific manufacturer
specific manufacturer
identification
.
identification
.
• For example, if there is a requirement
that the safety arming pin has a red flag • For example, if there is an expectation
with the words “Remove Before Flight” that the safety arming pin has a red flag
stenciled on the flag in black letters, a with the words “Remove Before Flight”
visual inspection of the arming pin flag stenciled on the flag in black letters, a
can be used to determine if this visual inspection of the arming pin flag
requirement was met. Inspection can can be used to determine if this
include inspection of drawings, expectation has been met.
documents, or other records.

Test
• The use of an end product to obtain • The use of an end product to obtain
verify detailed data needed to determine a
detailed data needed to
behavior or provide sufficient
performance
or provide
determine a
information to
sufficient information to verify
behavior t
hrough further
performance through further analysis.
analysis.
• Testing can be conducted on final end
products, breadboards, brassboards, • Testing can be conducted on final end
or prototypes. Testing produces data products, breadboards, brassboards,
at discrete points for each specified or prototypes. Testing produces
requirement under controlled information at discrete points for each
conditions and is the most resource- specified expectation under
intensive verification technique. As controlled conditions and is the most
the saying goes, “Test as you fly, and resource-intensive validation
fly as you test.” technique.

Other types
• Review of Design • Process Control:
• When verification is achieved: • Process control values are accepted
as evidence of requirements
• by validation of records or
compliance.
• by evidence of validated design
documents or • Process factors are known, measured,
• when approved design reports, and held to predetermined targets.
technical descriptions, engineering
• It is used to show dependability and
drawings unambiguously show the
consistency of process results.
requirement is met, the method shall
Process Control cannot be used to
be referred as “Review-of-design”.
show that a system/component
design complies with requirements.

Methods of V&V
4 FUNDAMENTAL METHODS DESCRIPTION
➢ Visual examination of drawings or data
➢ Examining a direct physical attribute of the item itself
• dimensions
INSPECTION
• weight
• physical characteristics
• color or markings
➢ Evaluation of data by generally accepted analytical techniques
• systems engineering analysis
• Statistics
• qualitative analysis
ANALYSIS
• analog modeling
• Similarity
• computer and hardware simulation
➢ Can also be evaluation of data derived from lower-level verifications.
➢ Showing that the use or operation achieves the results without detailed data
DEMONSTRATION
gathering. Utilize physical models or mockups.
➢ Often associated with the “ilities” (accessibility, transportability, serviceability, etc.)
➢ Operation of equipment during controlled conditions or when subjected to specified
TEST
operational environments to evaluate performance
➢ Test is the preferred method of V&V
17

Other Methods of V&V
ADDITONAL METHODS DESCRIPTION
➢ Assessing by review of prior acceptance data that a system is similar or identical in design
& manufacturing process to another system that has been previously qualified
➢ previous and current system predicted, or actual environments are similar
➢ Usually considered a subset of Analysis
SIMILARITY
➢ Is not used when either, or both, of the following conditions exist:
• The similar item used in the assessment was itself verified using similarity as the
method
• Items of criticality 1 or 1R (i.e., loss of vehicle, life, or serious injury)
➢ The use of vendor-furnished manufacturing or processing records to ensure
VALIDATION OF RECORDS requirements have been met
➢ Often used for COTS products or products purchased to standards
• There are differing definitions within the community of practice.
• The key is for your Project to establish agreed-to definitions, then be
consistent in using the terminology!
18

Choosing a V&V Method
Provide
Programmatic
➢Cost, risk, schedule, etc.
method
Requirements
suggestion to
Requirements
Developer
➢Review these to look for any
User/Payload
verification method required by the
Planner Guides
launch vehicle/carrier
Assess
Input from Requirements OR
Designers, Analysts, to choose a
& Technicians Method
Provide
System
comments to
Requirements
method(s)
chosen by
Experience
➢Research what methods have been used for Requirements
Database
similar requirements on other Projects. Developer
19

Choosing a V&V Method
Demonstration used when:
Test used when
:
*Verification of designed functions can be
*Analytical techniques do not produce adequate
performed through observation
results
*Results tend to be “pass/fail”, “yes/no”
*Failure modes exist which compromise safety,
space systems or mission objectives *Requirements are more subjective in nature such
as human factors or maintainability
*Components associated with critical system
interfaces *Uses actual or representative flight systems
Analysis is used when:
Inspection is used when:
*Accurate analytical techniques are possible
*Drawings, documents or data can be visually
checked to verify that the physical characteristics *Test is not a cost effective option
have been designed into the product
*Verification by inspection is not adequate
*Typically used for design features, construction
*Analytical techniques and models have been
methods, workmanship, dimensions and records
validated
20

21

Success Criteria
https://ndiastorage.blob.core.usgovcloudapi.net/ndia/2011/tes
t/11570MondayScukanec.pdf
22

MSFC-HDBK-3173
Success Criteria
• The Product Verification/Product Validation success criteria provide
the detailed and specific criteria that determine the successful
completion of the verification/validation planning activities.
• Product Verification/Product Validation success criteria are
submitted as part of the PDR data package (ideally) and
established (prepared) at least 90 days prior to the start of the
verification/validation activity to provide sufficient time to develop
and publish the procedures.
23

1 - Define success criteria
• Develop success criteria based on the following considerations:
• Performance criteria
• Environment Test Limits
• Tolerances
• Margins
• Specifications
• Restrictions
• Checkpoints
• Effectiveness and localization
24

2 - Submit the completed Success Criteria for
approval
• Obtain approval from the project team that the Product
Verification/Product Validation Success Criteria have reached sufficient
maturity to be used.
• Success Criteria should be prepared to be placed under formal
configuration control in accordance with established configuration
management procedures
25

3 - Manage and maintain the Success Criteria
• Manage and maintain the Success Criteria according to the guidance
contained in the planning information.
• Success Criteria are placed under formal configuration control in
accordance with established configuration management procedures.
26

27

28

29

30

31

32

33

34

35

Final Remarks
36

Test Mission
S
D
O
|     | Demonstration | H   |     | System |     |     |     |     |     |
| --- | ------------- | --- | --- | ------ | --- | --- | --- | --- | --- |
T
E
M
|     | Inspection |     |     | Segment |     |     |     |     |     |
| --- | ---------- | --- | --- | ------- | --- | --- | --- | --- | --- |
Analysis Element
|                         | Process Control  | Subsystem |     |     |     |     |     |     |     |
| ----------------------- | ---------------- | --------- | --- | --- | --- | --- | --- | --- | --- |
|                         | Review of Design | Component |     |     |     |     |     |     |     |
| Verification of Records |                  | Part      |     |     |     |     |     |     |     |
Similarity
STAGES
|     |     |     |     | Development |     | Qualification | Acceptance | Pre-Launch | In Orbit |
| --- | --- | --- | --- | ----------- | --- | ------------- | ---------- | ---------- | -------- |
DM
TECHNICALS
|     | EM  |     |     | MDR PDR | CDR |     |     | FRR | ORR |
| --- | --- | --- | --- | ------- | --- | --- | --- | --- | --- |
REVIEWS
RFM SM TM
PHASE D
QM
|     |     |     | PHASE A | PHASE B | PHASE C |     |     |     |     |
| --- | --- | --- | ------- | ------- | ------- | --- | --- | --- | --- |
PHASE E/F
| PFM | FM  |           | Viability  | Preliminary  | Detailed   |     |     |            |                         |
| --- | --- | --------- | ---------- | ------------ | ---------- | --- | --- | ---------- | ----------------------- |
|     |     |           |            |              |            |     | AIT | PRE-LAUNCH | Operations and Disposal |
|     |     |           | Analysis   | Desin        | Design     |     |     |            |                         |
|     |     |           |            | Logical      | Delivered  |     |     |            |                         |
|     |     | BASELINES |            |              |            |     |     | As built   |                         |
|     |     |           |            | Architecture | Product    |     |     |            |                         |
(project)
|     |     |     | Functional   |     | Physical     |     |     |     |     |
| --- | --- | --- | ------------ | --- | ------------ | --- | --- | --- | --- |
|     |     |     | Architecture |     | Architecture |     |     |     |     |
37

relações
SYSTEM OF
INTEREST
CONOPS Level Test Article
REQUIREMENTS V&V Method Stage
Model
Test
Enabling
Baseline
Systems
Facility
Plans
Procedure
Documentation Execution
38

Assignments
•
| Get                          | the Requirements |        |                |         |            |
| ---------------------------- | ---------------- | ------ | -------------- | ------- | ---------- |
| • Add                        | the Verication   | Method | & Verification | Success | Criteria   |
| • Review / Reorganize in one |                  |        | spreadsheet    | adding  | the levels |
• Indicate which System element (mis/sys/subsys/comp) will be involved
Grading Criteria:
1. Coherent Method x Success
2. Level Reorganization
3. Reading of the function and indicates
the target subsystem in subsystem level
(xx xx)
Group
Add verification
4. Suggestions for rewriting requirements,
to be verifiable
| Raw | Requirements |     |     |     |     |
| --- | ------------ | --- | --- | --- | --- |

PBS
Mission Find
Vampires
System
Ground
Satellite
Segment
Mission Data
Satellite Bus Payload Antenna
Control Distribution
Subsytem? Stru EPS AOCS OBDH TT&C Sensor 1 Camera XYZ
Component?
40

WHAT YOU MUST DO:
1. CREATE THE CONOPS
1. Get/Draw/Describe the concept of operations.
2. Review 15 REQUIREMENTS WITH THEIR RATIONALES
1. Place 3 requirements on Mission (user) Level that will relate to your Systems, 5 on System (System of Interest) Level (2
functional at least), and 7 on Subsystem Level
3. WRITE THE V&V DATA TO EACH REQUIREMENT
1. Indicate how each requirement will be verified,
2. Success Criteria (Use the template)
3. Create the DVM
4. PREPARE A PREENTATION
41