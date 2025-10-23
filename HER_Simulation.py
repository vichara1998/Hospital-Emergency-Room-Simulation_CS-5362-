import random
import simpy
import numpy as np

# Configuration parameters
NUM_DOCTORS = 7
AVG_CONSULTATION_TIME = 12  # minutes
PATIENT_ARRIVAL_INTERVAL = 2  # minutes
SIMULATION_TIME = 120  # total time in minutes

# Metrics
patients_treated = 0
total_wait_time = 0
wait_times = []

class HealthcareSystem:
    """Simulates a healthcare facility with doctors and patients"""
    
    def __init__(self, env, num_doctors, consultation_time):
        self.env = env
        self.doctors = simpy.Resource(env, num_doctors)
        self.consultation_time = consultation_time
        
    def consultation(self, patient_name, severity):
        """Simulate a patient consultation with variable time based on severity"""
        time_multiplier = 0.7 if severity == 1 else (1.0 if severity == 2 else 1.5)
        consultation_duration = max(5, np.random.normal(
            self.consultation_time * time_multiplier, 4))
        
        yield self.env.timeout(consultation_duration)
        print(f"  ✓ Consultation completed for {patient_name} at {self.env.now:.1f} min "
              f"(Duration: {consultation_duration:.1f} min)")

def patient_visit(env, name, healthcare_system, arrival_time):
    """Simulate a patient's journey through the healthcare system"""
    global patients_treated, total_wait_time
    
    # Assign random severity
    severity = random.choices([1, 2, 3], weights=[0.5, 0.3, 0.2])[0]
    severity_label = ["Low", "Medium", "High"][severity - 1]
    
    print(f"\n→ Patient {name} arrives at {env.now:.1f} min [Severity: {severity_label}]")
    
    with healthcare_system.doctors.request() as request:
        yield request
        
        wait_time = env.now - arrival_time
        total_wait_time += wait_time
        wait_times.append(wait_time)
        
        print(f"  • Patient {name} sees doctor at {env.now:.1f} min (Waited: {wait_time:.1f} min)")
        
        yield env.process(healthcare_system.consultation(name, severity))
        
        print(f"  ← Patient {name} discharged at {env.now:.1f} min")
        patients_treated += 1

def patient_generator(env, num_doctors, consultation_time, arrival_interval):
    """Generate patient arrivals throughout the simulation"""
    healthcare_system = HealthcareSystem(env, num_doctors, consultation_time)
    patient_id = 1
    
    # Initial patients already waiting
    for i in range(3):
        env.process(patient_visit(env, f"P{patient_id}", healthcare_system, env.now))
        patient_id += 1
    
    # Continuous arrivals
    while True:
        interval = max(1, np.random.poisson(arrival_interval))
        yield env.timeout(interval)
        env.process(patient_visit(env, f"P{patient_id}", healthcare_system, env.now))
        patient_id += 1

# --- Run Simulation ---
print("=" * 70)
print("HEALTHCARE SYSTEM SIMULATION")
print("=" * 70)
print(f"Configuration:")
print(f"  • Doctors available: {NUM_DOCTORS}")
print(f"  • Average consultation time: {AVG_CONSULTATION_TIME} minutes")
print(f"  • Patient arrival interval: ~{PATIENT_ARRIVAL_INTERVAL} minutes")
print(f"  • Simulation duration: {SIMULATION_TIME} minutes ({SIMULATION_TIME/60:.1f} hours)")
print("=" * 70)

env = simpy.Environment()
env.process(patient_generator(env, NUM_DOCTORS, AVG_CONSULTATION_TIME, PATIENT_ARRIVAL_INTERVAL))
env.run(until=SIMULATION_TIME)

# --- Display Results ---
print("\n" + "=" * 70)
print("SIMULATION RESULTS")
print("=" * 70)

avg_wait = total_wait_time / max(1, patients_treated)
throughput_per_hour = int((patients_treated / SIMULATION_TIME) * 60)  # per hour, rounded to integer

print(f"Total patients treated: {patients_treated}")
print(f"Average wait time: {avg_wait:.2f} minutes")
print(f"Maximum wait time: {max(wait_times) if wait_times else 0:.2f} minutes")
print(f"Doctor utilization: {(patients_treated * AVG_CONSULTATION_TIME) / (SIMULATION_TIME * NUM_DOCTORS) * 100:.1f}%")
print(f"Throughput (patients/hour): {throughput_per_hour}")
print("=" * 70)
