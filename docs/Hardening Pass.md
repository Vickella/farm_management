I have wsl / ubuntu running on my local pc and my site is test.local. There are the issues i found in my live testing. I want you to address those issues, in doing so think systematically, with user experience, farmings operations and accounting expertise especially IAS 41 on top to produce high quality app. After you are done with the fixing, push to github and pull in wsl and test the changes on the live developemt site. ... You have to test each and every doctype and functionality. Note the errors or issues which you will be getting and address them. For anything related to other core module for example sales, journals, stock, etc you have to go and follow up to mmake sure that functionality is solid as well as the reports are sound. Treat this as an iteratiive process to pass this app into production. Let your main focus be on highlighted issues and any other which might be linked to them. My github username is Vickella and my key is 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 because the repo is private, you might need these when pulling in wsl....... Execute, please first read and understand the highlighted issues and brainstorm first how to implemet based on what you first understood about the codebase. Then after you are done everything, write a Production Codebase Report. 

1. Fields in Biological Asset must be reactive based on the Farm type selected. I dont expect :
	Quantity
	Acquisition Date
	acquisition_date
	Quantity
	quantity
	Unit

	Head
	unit
	Average Weight Kg
	average_weight_kg
	Mortality To Date
To be there on a Crop Production biological asset.
 
2. In Biological Asset, Managed Crop / Animal / Species must give select options filtered based on Asset Category or Farm Type, I dont expect to see Brahman if i could have selected a Crop Production or any unrealated Fram type or asset category.

3. In Harvest Transaction, there is an error: Harvest quantity cannot exceed Biological Asset quantity.... This must be resolved systematically especially for Crop Production, its difficult to determine initial quantity but one can declare the Kgs/ tonnes or any measure produced eg 12 tonnes of tobacco but the initial quantity can not be upto that.
	To determine initial cost which the harvest must be posted with or the biological asset, user must create a Farm BOM which will be the initial cost for the project. However this might create difficulties in determining the cost per unit of harvested items since the initial quantity is of the inputs and other things not of the out put. This need to be addressed especially for crops since animals can be allocated per unit / per head or bird... I got the following error: 
Valuation Rate for the Item Tobbaco, is required to do accounting entries for Stock Entry MAT-STE-2026-00001.

Here are the options to proceed:
If the item is transacting as a Zero Valuation Rate item in this entry, please enable 'Allow Zero Valuation Rate' in the Stock Entry Item table.
If not, you can Cancel / Submit this entry after performing either one below:
Create an incoming stock transaction for the Item.
Mention Valuation Rate in the Item master.

Check the following logic, it must be implemented within our existing doctypes. I think to add initial costs, we use ther Farm BOM, then when we add our Biological Asset, on initial cost, we select the BOM. In our Farm BOM where project type = Crop Production, Planned quantity is planned size and does not related to item that will be harvested. Check the following logic: 

ACCOUNTING DOCUMENTATION: BIOLOGICAL ASSETS AND HARVEST INVENTORY
For Crop-Based and Agriculture Projects where Initial Quantity and Cost per Unit Cannot Be Reliably Measured

1. PURPOSE

This documentation explains how biological assets and harvested agricultural produce should be accounted for in agriculture projects such as tobacco farming, fish farming, crop production, poultry, livestock fattening, horticulture, and similar projects.

It is especially useful where, at the beginning of the project, the final harvest quantity and cost per unit cannot be measured reliably.

Examples include:

- Tobacco: planted hectares are known, but final cured kilograms are unknown.
- Fish farming: fingerlings are stocked, but final harvest weight is unknown.
- Maize or horticulture: field size is known, but final yield is uncertain.
- Poultry: chicks are stocked, but final saleable weight or mortality is uncertain.

The accounting treatment separates the project into two main phases:

Phase 1: Before harvest
The living crop, fish, poultry, or animal is treated as a biological asset under IAS 41.

Phase 2: At and after harvest
The harvested produce becomes inventory and is accounted for under IAS 2.


2. KEY ACCOUNTING PRINCIPLE

Before harvest, the asset is still living and undergoing biological transformation. Therefore, it is accounted for as a biological asset.

At harvest, the agricultural produce is separated from the biological asset. At that point, the harvested produce is measured and transferred to inventory.

The key rule is:

Before harvest:
Value the living asset under IAS 41.

At harvest:
Transfer harvested produce to inventory at fair value less costs to sell.

After harvest:
Apply IAS 2 inventory costing.


3. WHEN INITIAL QUANTITY AND UNIT COST CANNOT BE MEASURED RELIABLY

In many agriculture projects, it is not practical to determine a reliable unit cost at the start.

For example, in tobacco farming, the farmer may know that five hectares were planted, but they may not yet know:

- Final harvested kilograms
- Final grade
- Expected price per kilogram
- Losses due to weather, pests, curing, or handling
- Final saleable quantity

In fish farming, the farmer may know the number of fingerlings stocked, but may not yet know:

- Mortality rate
- Final harvest weight
- Growth performance
- Feed conversion outcome
- Market price at harvest

Because of this, the system should not force initial stock quantity and cost per unit at the beginning of the project.

Instead, costs should first be accumulated against the project, batch, pond, field, or biological asset account.


4. BEFORE HARVEST: COST ACCUMULATION STAGE

During the growing or production stage, costs are accumulated against the biological asset.

Examples of costs before harvest include:

- Seeds
- Seedlings
- Fingerlings
- Fertiliser
- Chemicals
- Feed
- Veterinary costs
- Field labour
- Farm labour
- Irrigation
- Water
- Electricity used directly in production
- Pond preparation
- Land preparation
- Crop protection
- Agronomy services
- Direct production supervision

These costs are posted to the biological asset account or biological asset project.

Journal entry:

Dr Biological Asset - Tobacco Crop / Fish Stock / Crop Project
   Cr Cash / Payables / Stores / Payroll

Example:

Fertiliser purchased for tobacco field: $800

Dr Biological Asset - Tobacco Crop       800
   Cr Cash / Payables                    800

This builds the carrying amount of the biological asset when fair value is not yet reliably measurable.


5. WHEN FAIR VALUE BECOMES RELIABLE

As the project matures, fair value may become easier to estimate.

Fair value may become reliable when the entity can reasonably estimate:

- Expected harvest quantity
- Expected selling price
- Expected grade or quality
- Remaining costs to complete
- Costs to sell
- Market demand
- Contract price or auction price

A practical fair value estimate may be calculated as follows:

Expected gross sale value
less remaining costs to complete
less costs to sell
= fair value less costs to sell

Example:

Expected tobacco harvest:                  2,000 kg
Expected selling price:                    $4.00 per kg
Expected gross sale value:                 $8,000
Less remaining harvest and curing costs:   $1,500
Less estimated selling costs:              $500

Fair value less costs to sell:             $6,000

If the current carrying amount is different from the fair value less costs to sell, only the movement is posted.

If fair value less costs to sell is higher than the carrying amount:

Dr Biological Asset
   Cr Fair Value Gain - Biological Asset

If fair value less costs to sell is lower than the carrying amount:

Dr Fair Value Loss - Biological Asset
   Cr Biological Asset

Example:

Accumulated costs to date:                 $3,500
Fair value less costs to sell:             $6,000
Fair value gain:                           $2,500

Journal:

Dr Biological Asset - Tobacco Crop          2,500
   Cr Fair Value Gain - Biological Asset    2,500

The biological asset is now carried at $6,000.

Important:

The system must not add the fair value on top of the existing balance incorrectly.

Correct treatment:

Current carrying amount:                   $3,500
Adjustment to fair value:                  $2,500
New carrying amount:                       $6,000

Incorrect treatment:

Accumulated cost:                          $3,500
Plus fair value:                           $6,000
Wrong asset value:                         $9,500

Only the movement should be posted.


6. AT HARVEST: TRANSFER FROM BIOLOGICAL ASSET TO INVENTORY

At harvest, the biological asset becomes agricultural produce.

Examples:

- Tobacco plants become harvested tobacco leaves.
- Fish stock becomes harvested fish inventory.
- Maize crop becomes harvested maize grain.
- Horticulture crop becomes harvested vegetables.
- Poultry becomes processed or live bird inventory depending on the business model.

At this stage, the harvested quantity is known or can be measured.

The harvested produce is measured at fair value less costs to sell at the point of harvest.

This amount becomes the deemed cost of inventory.

Formula:

Inventory value at harvest = Fair value less costs to sell at harvest

Cost per unit = Inventory value at harvest / Harvested quantity


7. TOBACCO EXAMPLE

Assume:

Tobacco project: Field A
Accumulated costs before harvest:          $3,500
Fair value less costs to sell at harvest:  $6,000
Harvested quantity:                        2,000 kg

Step 1: Adjust biological asset to harvest fair value

Current carrying amount before harvest:    $3,500
Required carrying amount at harvest:       $6,000

Fair value gain:

$6,000 - $3,500 = $2,500

Journal:

Dr Biological Asset - Tobacco Crop          2,500
   Cr Fair Value Gain - Biological Asset    2,500

Step 2: Transfer harvested tobacco to inventory

Dr Inventory - Tobacco Leaves               6,000
   Cr Biological Asset - Tobacco Crop       6,000

Step 3: Calculate inventory cost per kg

Cost per kg = $6,000 / 2,000 kg
Cost per kg = $3.00 per kg

Stock entry:

Item: Tobacco Leaves
Quantity: 2,000 kg
Rate: $3.00 per kg
Amount: $6,000


8. FISH FARMING EXAMPLE

Assume:

Fish pond project: Pond 1
Accumulated feed, labour, water, and fingerling costs: $4,800
Fair value less costs to sell at harvest:              $7,500
Harvested fish quantity:                               1,500 kg

Step 1: Adjust biological asset to fair value

Fair value gain:

$7,500 - $4,800 = $2,700

Journal:

Dr Biological Asset - Fish Stock             2,700
   Cr Fair Value Gain - Biological Asset     2,700

Step 2: Transfer harvested fish to inventory

Dr Inventory - Harvested Fish                7,500
   Cr Biological Asset - Fish Stock          7,500

Step 3: Calculate cost per kg

Cost per kg = $7,500 / 1,500 kg
Cost per kg = $5.00 per kg

Stock entry:

Item: Harvested Fish
Quantity: 1,500 kg
Rate: $5.00 per kg
Amount: $7,500


9. WHAT IF FAIR VALUE CANNOT BE MEASURED RELIABLY BEFORE HARVEST?

If fair value cannot be measured reliably during early growth, the biological asset may be carried at accumulated cost, less impairment where applicable, until fair value becomes reliably measurable.

This is common in early stages where:

- The crop is too immature.
- Yield cannot be estimated.
- There is no reliable market price.
- Grade or quality is unknown.
- Mortality or loss rate is uncertain.
- There is no active market for the immature biological asset.

In such cases, continue accumulating direct production costs.

Journal:

Dr Biological Asset - Crop / Fish / Livestock Project
   Cr Cash / Payables / Stores / Payroll

When fair value later becomes reliable, remeasure the biological asset and post only the movement.


10. POST-HARVEST COSTS

After harvest, the harvested produce is no longer a biological asset. It is inventory.

IAS 2 applies after harvest.

Post-harvest costs may be capitalised into inventory if they are necessary to bring the inventory to its present location and condition.

Examples of capitalisable post-harvest costs:

- Tobacco curing
- Grading
- Baling
- Packaging
- Processing
- Cold storage
- Handling
- Transport from field to warehouse
- Transport to auction floor if required to make the product saleable
- Direct labour for processing or packaging

Journal:

Dr Inventory - Tobacco / Fish / Agricultural Produce
   Cr Cash / Payables / Payroll / Stores

Example:

Tobacco curing and packaging costs: $1,200

Dr Inventory - Tobacco Leaves       1,200
   Cr Cash / Payables               1,200

Updated inventory cost:

Original harvest value:             $6,000
Post-harvest costs:                 $1,200
Total inventory cost:               $7,200
Quantity:                           2,000 kg

Updated cost per kg:

$7,200 / 2,000 kg = $3.60 per kg


11. COSTS THAT SHOULD NOT BE CAPITALISED INTO INVENTORY

Not every cost after harvest should be added to inventory.

The following are normally expensed:

- General administration costs
- Marketing costs
- Selling commissions
- Delivery to customer after sale
- Abnormal wastage
- Avoidable inefficiencies
- Penalties
- General overheads not directly related to production
- Financing costs unless specific criteria are met

Example:

Sales commission paid after tobacco sale: $300

Dr Selling Expenses                 300
   Cr Cash / Payables               300


12. SALE OF HARVESTED INVENTORY

When the produce is sold, revenue and cost of sales are recognised.

Step 1: Recognise revenue

Dr Cash / Trade Receivables
   Cr Sales Revenue

Step 2: Recognise cost of sales

Dr Cost of Sales
   Cr Inventory - Tobacco / Fish / Produce

Example:

Sold 500 kg tobacco
Inventory cost per kg: $3.60
Cost of sales:

500 kg x $3.60 = $1,800

Journal:

Dr Cost of Sales                    1,800
   Cr Inventory - Tobacco Leaves    1,800


13. RECOMMENDED ERP SYSTEM LOGIC

The system should support the following process:

1. Create Biological Asset Project

Examples:

- Tobacco Field A 2026
- Fish Pond 1 Batch 2026
- Maize Field B 2026
- Poultry Batch 2026

The system should allow the project to be created without forcing an opening stock quantity or unit cost where these cannot be measured reliably.

2. Accumulate Costs

All direct production costs are posted to the biological asset project or batch.

3. Optional Fair Value Valuation

When fair value becomes reliable, the system should calculate fair value less costs to sell and compare it with the current carrying amount.

Only the movement should be posted.

4. Harvest Document

At harvest, the system should capture:

- Harvest date
- Biological asset project
- Harvested item
- Harvested quantity
- Unit of measure
- Fair value less costs to sell at harvest
- Calculated cost per unit
- Warehouse
- Batch number where applicable

5. Harvest Journal and Stock Entry

The system should transfer the biological asset to inventory at harvest value.

Journal:

Dr Inventory - Harvested Produce
   Cr Biological Asset

Stock entry:

Quantity = harvested quantity
Rate = harvest value / harvested quantity
Amount = harvest value

6. Post-Harvest Cost Allocation

The system should allow costs such as curing, grading, packaging, and processing to be allocated to the harvested inventory.

This updates the inventory cost per unit.

7. Sale

On sale, the system should reduce inventory and recognise cost of sales.


14. IMPORTANT SYSTEM CONTROLS

The system should prevent the following mistakes:

- Creating inventory before harvest quantity is known.
- Forcing unreliable unit costs at project start.
- Double counting accumulated costs and fair value.
- Adding fair value on top of existing carrying amount instead of posting only the movement.
- Transferring inventory at accumulated cost where fair value at harvest is available.
- Mixing biological asset costs with post-harvest inventory costs.
- Capitalising selling commissions and general administration expenses into inventory.
- Allowing harvest stock entry without a matching biological asset transfer.
- Allowing negative or zero harvest quantity where inventory value is being transferred.
- Allowing unexplained difference between biological asset carrying amount and harvest transfer value.


15. SUMMARY ACCOUNTING FLOW

Before harvest:

Dr Biological Asset
   Cr Cash / Payables / Stores / Payroll

Fair value gain before harvest:

Dr Biological Asset
   Cr Fair Value Gain - Biological Asset

Fair value loss before harvest:

Dr Fair Value Loss - Biological Asset
   Cr Biological Asset

At harvest:

Dr Inventory - Harvested Produce
   Cr Biological Asset

Post-harvest costs:

Dr Inventory - Harvested Produce
   Cr Cash / Payables / Payroll / Stores

Sale:

Dr Cash / Trade Receivables
   Cr Sales Revenue

Cost of sales:

Dr Cost of Sales
   Cr Inventory - Harvested Produce


16. SIMPLE FINAL EXAMPLE

Tobacco Field A

Growing costs incurred:

Seeds, fertiliser, labour, chemicals: $3,500

Journal:

Dr Biological Asset - Tobacco Crop       3,500
   Cr Cash / Payables                    3,500

At harvest, fair value less costs to sell is $6,000.
Harvested quantity is 2,000 kg.

Fair value gain:

$6,000 - $3,500 = $2,500

Journal:

Dr Biological Asset - Tobacco Crop       2,500
   Cr Fair Value Gain                    2,500

Transfer to inventory:

Dr Inventory - Tobacco Leaves            6,000
   Cr Biological Asset - Tobacco Crop    6,000

Cost per kg:

$6,000 / 2,000 kg = $3.00 per kg

Post-harvest curing and packaging costs: $1,200

Journal:

Dr Inventory - Tobacco Leaves            1,200
   Cr Cash / Payables                    1,200

Updated inventory value:

$6,000 + $1,200 = $7,200

Updated cost per kg:

$7,200 / 2,000 kg = $3.60 per kg

Sale of 500 kg:

Cost of sales:

500 kg x $3.60 = $1,800

Journal:

Dr Cost of Sales                         1,800
   Cr Inventory - Tobacco Leaves         1,800

This gives a clean accounting treatment where the biological asset is managed before harvest, inventory is recognised only when quantity becomes reliable, and cost per unit is calculated only when harvested quantity is known.

4. In Animal Stock Entry, if i choose sale or other related types and pick the Biological Asset, other fields must be automatically be filled such as Animal, Breed, Unit Cost / Rate.
I did the following Animal Stock Entry: App Logo
Animal Stock Entry
ASE-0002
Search or type a command (Ctrl + G)
Begin typing for results.
No new notifications
Help 

A

ASE-0002
Submitted
 Assigned To
 Attachments
 Tags
 Share
0
·
0
Follow
You last edited this · 13 minutes ago
You created this · 13 minutes ago
Posting Date
06-22-2026
posting_date
Entry Type
Sale
entry_type
Status
Submitted
status
Farm
A1 Farm
farm
Biological Asset
BA-0002
biological_asset
Project
Test
project
Movement Details
Animal
Cattle
species
Breed
Brahman
breed
Individual Animal
LI-0002
livestock_individual
Quantity
5
quantity
Unit
Head
unit
Unit Cost / Rate
$ 300.00
rate
Total Amount
$ 1,500.00
amount
Cost and Accounting
Sale Proceeds Amount
$ 3,000.00
sale_amount
Asset Value Reduction
$ 32.81
asset_value_reduction
Outflow Journal Entry
ACC-JV-2026-00006
journal_entry
Sale Proceeds Journal Entry
ACC-JV-2026-00007
sale_journal_entry....... where is Asset Value Reduction
$ 32.81 coming from??????


Improvement Rule, leave only relevant entry types, others seem duplicated and unnecessary: Opening
Receipt
Purchase
Birth
Transfer In
Issue
Sale
Death
Transfer Out
Adjustment Increase
Adjustment Decrease
Cost Capitalization

Remove
Adjustment Increase
Adjustment Decrease
Cost Capitalization

# Transfer In and Transfer Out let them be just one "Transfer", then indicate the source and target Farm.

### Purchase and Sale let them pass through the standard sorce documents (Sales Invoice and purchase Invoice) not journals... The rates and quanities used be the valuation or costs for the Stock Entry values.

Using what we have built so far take some notes here and refactor what needs to be refactored

# Accounting Treatment of Livestock Biological Assets

## 1. Purpose

This document explains the accounting treatment of livestock such as cattle, pigs, goats, sheep, broiler birds, layers, and similar living animals.

Livestock is treated as a **biological asset** while it is alive. Under IAS 41, biological assets are generally measured at **fair value less costs to sell**, and fair value movements are recognised in profit or loss. Agricultural produce harvested from biological assets is measured at fair value less costs to sell at the point of harvest.

---

## 2. Key Principle

Living animals are not automatically inventory, even when they are held for sale.

The basic rule is:

```text
Living animal = Biological Asset
Harvested output from the animal = Inventory
Processed animal product = Inventory
Animal sold alive = Biological Asset disposed directly on sale
```

Examples:

```text
Live cattle held for sale = Biological Asset
Live pigs held for sale = Biological Asset
Live broiler birds held for sale = Biological Asset
Milk collected from cows = Inventory
Eggs collected from layers = Inventory
Beef after slaughter = Inventory
Pork after slaughter = Inventory
Dressed chicken after processing = Inventory
```

---

## 3. Livestock Sold Alive

Where livestock is sold alive, there is no need to transfer the animal to inventory before sale.

The animal remains a biological asset until the date of sale.

### Example: Cattle Sold Alive

Assume:

```text
Cost of calf / accumulated rearing cost:       $400
Fair value less costs to sell at reporting:    $650
Final selling price:                           $700
```

Initial recognition:

```text
Dr Biological Asset - Cattle        400
   Cr Cash / Payables               400
```

Fair value adjustment:

```text
Fair value gain = 650 - 400 = 250
```

```text
Dr Biological Asset - Cattle        250
   Cr Fair Value Gain - Livestock   250
```

Sale of live cattle:

```text
Dr Cash / Trade Receivable          700
   Cr Livestock Sales Revenue       700
```

Derecognise biological asset:

```text
Dr Cost of Sales - Livestock        650
   Cr Biological Asset - Cattle     650
```

The profit on final sale is:

```text
Sales revenue                       700
Less carrying amount                650
Profit on sale                       50
```

The earlier fair value gain of $250 was already recognised before sale.

---

## 4. Birds Sold Alive

For broiler birds sold alive, the same principle applies. They remain biological assets until sold.

Assume:

```text
Accumulated cost of chicks, feed, labour, vaccines:   $2,000
Fair value less costs to sell before sale:            $2,800
Selling price:                                        $3,000
```

Cost accumulation:

```text
Dr Biological Asset - Broiler Birds       2,000
   Cr Cash / Payables / Stores            2,000
```

Fair value gain:

```text
Dr Biological Asset - Broiler Birds         800
   Cr Fair Value Gain - Biological Asset    800
```

Sale:

```text
Dr Cash / Trade Receivable                3,000
   Cr Sales Revenue - Live Birds          3,000
```

Derecognise asset:

```text
Dr Cost of Sales - Live Birds             2,800
   Cr Biological Asset - Broiler Birds    2,800
```

No inventory transfer is posted because the birds were sold alive.

---

## 5. Livestock Slaughtered or Processed Before Sale

If the livestock is slaughtered or processed before sale, then the animal changes from a living biological asset into inventory.

Examples:

```text
Cattle slaughtered into beef
Pig slaughtered into pork
Chicken processed into dressed chicken
Goat slaughtered into meat
```

At slaughter or processing, the resulting produce is measured at fair value less costs to sell at the point of harvest or slaughter. After that point, IAS 2 inventory accounting applies.

### Example: Cattle Slaughtered for Beef

Assume:

```text
Carrying amount of cattle before slaughter:      $650
Fair value less costs to sell of beef produced:  $700
```

First adjust the biological asset if required:

```text
Dr Biological Asset - Cattle             50
   Cr Fair Value Gain - Livestock        50
```

Transfer to inventory:

```text
Dr Inventory - Beef / Carcass           700
   Cr Biological Asset - Cattle         700
```

Further processing, packaging, or cold storage costs may then be added to inventory if they are necessary to bring the inventory to its present condition and location.

```text
Dr Inventory - Beef Products
   Cr Cash / Payables / Payroll
```

---

## 6. Livestock Kept for Produce

Some animals are kept to produce agricultural produce while the animal remains alive.

Examples:

```text
Dairy cows produce milk
Layer birds produce eggs
Sheep produce wool
Breeding animals produce offspring
```

The animal remains a biological asset. The produce collected from the animal becomes inventory.

### Example: Dairy Cow Producing Milk

The cow remains in biological assets:

```text
Biological Asset - Dairy Cattle
```

When milk is collected:

```text
Dr Inventory - Milk
   Cr Agricultural Produce Gain / Milk Harvest Income
```

The milk is measured at fair value less costs to sell at the point of collection. After collection, IAS 2 applies.

---

## 7. Ongoing Livestock Costs

Costs such as feed, veterinary costs, labour, medication, bedding, and direct farm overheads may be accumulated against the livestock batch or recognised according to the entity’s accounting policy.

Examples:

```text
Feed
Vaccines
Veterinary treatment
Farm labour
Water
Electricity directly used in production
Animal transport before sale
```

Where fair value is reliably measurable, the main reporting value remains fair value less costs to sell, not accumulated cost alone.

Typical operational entry:

```text
Dr Biological Asset - Livestock
   Cr Cash / Payables / Stores / Payroll
```

At reporting date, the livestock should be remeasured to fair value less costs to sell.

If fair value increases:

```text
Dr Biological Asset - Livestock
   Cr Fair Value Gain - Livestock
```

If fair value decreases:

```text
Dr Fair Value Loss - Livestock
   Cr Biological Asset - Livestock
```

---

## 8. Recommended ERP System Logic

The system should allow each livestock record or batch to have a disposal method.

Recommended options:

```text
Sold Alive
Slaughtered / Processed
Kept for Produce
Breeding Stock
Culled / Lost / Died
```

The disposal method determines the accounting treatment.

### Sold Alive

```text
Dr Cash / Receivable
   Cr Sales Revenue

Dr Cost of Sales
   Cr Biological Asset
```

No inventory transfer is required.

### Slaughtered / Processed

```text
Dr Inventory - Meat / Processed Product
   Cr Biological Asset
```

Inventory is then sold under normal IAS 2 inventory rules.

### Kept for Produce

```text
Animal remains as Biological Asset
Produce collected becomes Inventory
```

Example:

```text
Dr Inventory - Milk / Eggs / Wool
   Cr Agricultural Produce Gain
```

### Death or Loss

If an animal dies or is lost, derecognise its carrying amount.

```text
Dr Livestock Loss / Mortality Expense
   Cr Biological Asset - Livestock
```

---

## 9. Summary

The key rule is:

```text
Livestock sold alive:
Biological Asset -> Sale

Livestock slaughtered:
Biological Asset -> Inventory -> Sale

Livestock producing output:
Biological Asset remains alive
Output becomes Inventory

Livestock lost or dead:
Biological Asset -> Loss Expense
```

Therefore, the system should not force all livestock into inventory. Live animals should remain biological assets until they are sold, slaughtered, processed, or otherwise disposed of.


6. In Farm BOM, Unit must validate the Default UOM of the selected item. Also we must pin a Farm BOM to a project mandatory. 
7. In Farm Budget, remove Actual and Variance fields. These must only be seen the Budget Variance report. In the Farm Budget we are only putting what we are expecting to use, the labour, items, etc. 
9. Then as we transact, doing our purchases and expenses against our projects these actuals will now be the values to use to create the budget variance report. There must be no manual capturing of actuals, they must come from actual transactions linked to that project.
10 Create Budget Forecasting Doctype that can be used to predict our spending in and year on a specific BOM and Project.
11. Create Standard Cost Calculation BOM doctype that works like the manufacturing BOM, that can be used to determine the cost of a project eg 100 broilers. This one is to be used only on specific projects were requirements, / inputs doesnt vary. Then Farm BOM will be used to capture the actual costs of the projects as discussed above around Biological Assets.


Contract Farming

This one needs proper handling. Contract farming can be in two ways. 

1. The farm may carry out a project on contract being given inputs and everything but a contacting company or person for example Tobacco Processing comapnies give farmers inputs. This one creates (deffered) liability on the farm.
2. The farm may give a contract to other farms / individuals (the one current implemented in this system). This one creates deffered assets for the farm.
In the case 1, we must get details of the supplier / contractor. 
So user has to pick the type of contract farm, whether if the farm is receiving or giving the contract and fields have to be reactive based on the choice.

In Input Loan Disbursement, the following must be in a table form as the inputs might be many.
Input Type
Seed
input_type
Item
Quantity
Unit
Value

In Contract Farming Agreement, the following must be in a table form: 
Inputs Provided

Seed Provided
seed_provided
Seed Value
seed_value

Fertilizer Provided
fertilizer_provided
Fertilizer Value
fertilizer_value

Chemical Provided
chemical_provided
Chemical Value
chemical_value

These things has to be tracked against what was then disbursed.

Do not hard code kg, put Unit: Production Target Kg
production_target_kg
Agreed Purchase Price Per Kg


Operations of contract farming must be will tracked to that we can be able to see whether we are profiting or not from the contacting farming.
I would like to achieve this but creating a Contract Farming cost center that comes on installtion by default, seperate income account for contract farming and others, all mapped in Farm Management Settings.

VERDICT: EXECUTE THIS CLEANLY AND WE ARE INTO PRODUCTION AND LAUNCH THIS APP, I HAVE TRIED TO TEST IT COMPREHENSIVELY. LETS GO BROO. YOU'RE ON FIRE.




 