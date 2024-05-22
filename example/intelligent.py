#   SPEC
#   Run as separated thread
#   Use schedules to call for train and analyze
#   The schedules located in mainfunctions
#   Train model 2 days after start - for recognize daily pattern for first week
#   Train model every week start after 1 week - to recognize weekly pattern
#   After model is trained, start schedule immediately
#   Analyze run daily at 1:00

# TRAIN FUNCTION LOGIC
# Import data from database
# Train model
# Save model as seperated file


# ANALYZE FUNCTION LOGIC
# Run model
# Matching device runtime to schedule and sensor
# Return automation to mainfunctions to save to file automations.txt
