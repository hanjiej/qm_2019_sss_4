import numpy as np

# initialized with a gas type
class Noble_Gas_Model:

    def __init__(self, gas_type):

        """model_parameters : a dictionary of parameters"""

        if isinstance(gas_type, str):

            self.gas_type = gas_type
        else:

            raise TypeError("Name should be a string!")

        if (self.gas_type.lower() == "ar" or self.gas_type.lower() == "argon"):
            self.model_parameters = {
            'r_hop' : 3.1810226927827516,
            't_ss' : 0.03365982238611262,
            't_sp' : -0.029154833035109226,
            't_pp1' : -0.0804163845390335,
            't_pp2' : -0.01393611496959445,
            'r_pseudo' : 2.60342991362958,
            'v_pseudo' : 0.022972992186364977,
            'dipole' : 2.781629275106456,
            'energy_s' : 3.1659446174413004,
            'energy_p' : -2.3926873325346554,
            'coulomb_s' : 0.3603533286088998,
            'coulomb_p' : -0.003267991835806299
            }

        elif (self.gas_type.lower() == "ne" or self.gas_type.lower() == "neon"):
            self.model_parameters = {
            'coulomb_p': -0.010255409806855187,
            'coulomb_s': 0.4536486561938202,
            'dipole': 1.6692376991516769,
            'energy_p': -3.1186533988406335,
            'energy_s': 11.334912902362603,
            'r_hop': 2.739689713337267,
            'r_pseudo': 1.1800779720963734,
            't_pp1': -0.029546671673199854,
            't_pp2': -0.0041958662271044875,
            't_sp': 0.000450562836426027,
            't_ss': 0.0289251941290921,
            'v_pseudo': -0.015945813280635074
            }

        else:
            raise TypeError("Gas type cannot be recognized: Ar, Argon, Ne and Neon expected")

        self.ionic_charge = 6

        self.orbital_types = ['s', 'px', 'py', 'pz']

        self.orbitals_per_atom = len(self.orbital_types)

        self.p_orbitals = ['px', 'py', 'pz']

        self.vec = { 'px':[1,0,0], 'py':[0,1,0], 'pz':[0,0,1] }

        self.orbital_occupation = {'s':0, 'px':1, 'py':1, 'pz':1}


    def ao_index(self, atom_p, orb_p):

        p = atom_p * self.orbitals_per_atom

        p += self.orbital_types.index(orb_p)

        return p


    def atom(self, ao_index):

        return ao_index // self.orbitals_per_atom


    def orb(self, ao_index):

        orb_index = ao_index % self.orbitals_per_atom

        return self.orbital_types[orb_index]


class HartreeFock:
    def __init__(self, atomic_coordinates, gas_model):
        self.atomic_coordinates = atomic_coordinates

        self.gas_model = gas_model

        self.ndof = len(self.atomic_coordinates) * self.gas_model.orbitals_per_atom

        self.chi_tensor = self.calculate_chi_tensor()

        self.potential_vector = self.calculate_potential_vector()

        self.interaction_matrix = self.calculate_interaction_matrix()

        self.density_matrix = self.calculate_atomic_density_matrix()

        self.hamiltonian_matrix = self.calculate_hamiltonian_matrix()

        self.fock_matrix = self.calculate_fock_matrix(self.density_matrix)


    def hopping_energy(self, o1, o2, r12):
        r12_rescaled = r12 / self.gas_model.model_parameters['r_hop']

        r12_length = np.linalg.norm(r12_rescaled)

        ans = np.exp( 1.0 - r12_length**2 )

        if o1 =='s' and o2 == 's':

            ans = ans * self.gas_model.model_parameters['t_ss']

        if o1 =='s' and o2 in self.gas_model.p_orbitals:

            ans = ans * np.dot(self.gas_model.vec[o2], r12_rescaled) * self.gas_model.model_parameters['t_sp']

        if o2 =='s' and o1 in self.gas_model.p_orbitals:

            ans = ans * -np.dot(self.gas_model.vec[o1], r12_rescaled) * self.gas_model.model_parameters['t_sp']

        if o1 in self.gas_model.p_orbitals and o2 in self.gas_model.p_orbitals:

            ans = ans * ( (r12_length**2) * np.dot(self.gas_model.vec[o1],self.gas_model.vec[o2]) * self.gas_model.model_parameters['t_pp2']
                     - np.dot(self.gas_model.vec[o1],r12_rescaled)* np.dot(self.gas_model.vec[o2],r12_rescaled)
                     * (self.gas_model.model_parameters['t_pp1'] + self.gas_model.model_parameters['t_pp2']) )

        return ans


    def coulomb_energy(self, o1, o2, r12):

        r12_length = np.linalg.norm(r12)

        ans = 1.0

        if o1 =='s' and o2 == 's':

            ans = ans * 1.0 / r12_length

        if o1 =='s' and o2 in self.gas_model.p_orbitals:

            ans = ans * np.dot(self.gas_model.vec[o2], r12) / r12_length**3

        if o2 =='s' and o1 in self.gas_model.p_orbitals:

            ans = ans * -np.dot(self.gas_model.vec[o1], r12) / r12_length**3

        if o1 in self.gas_model.p_orbitals and o2 in self.gas_model.p_orbitals:

            ans = ans * ( np.dot(self.gas_model.vec[o1],self.gas_model.vec[o2]) / r12_length**3
                     - 3.0 * np.dot(self.gas_model.vec[o1],r12)* np.dot(self.gas_model.vec[o2],r12) / r12_length**5 )

        return ans


    def pseudopotential_energy(self, o, r):

        r_rescaled = r / self.gas_model.model_parameters['r_pseudo']

        r_length = np.linalg.norm(r_rescaled)

        ans = self.gas_model.model_parameters['v_pseudo'] * np.exp( 1.0 - r_length**2 )

        if o in self.gas_model.p_orbitals:

            ans *= -2.0 * np.dot(self.gas_model.vec[o], r_rescaled)

        return ans


    def calculate_energy_ion(self):

        energy_ion = 0.0

        for i, r_i in enumerate(self.atomic_coordinates):

            for j, r_j in enumerate(self.atomic_coordinates):

                if i<j:

                    energy_ion += (self.gas_model.ionic_charge**2) * self.coulomb_energy('s', 's', r_i - r_j)

        return energy_ion


    def calculate_potential_vector(self):

        self.potential_vector = np.zeros(self.ndof)

        for p in range(self.ndof):

            for atom_i, r_i in enumerate(self.atomic_coordinates):

                r_pi = self.atomic_coordinates[self.gas_model.atom(p)] - r_i

                if atom_i != self.gas_model.atom(p):

                    self.potential_vector[p] += ( self.pseudopotential_energy(self.gas_model.orb(p), r_pi) -
                                        self.gas_model.ionic_charge * self.coulomb_energy(self.gas_model.orb(p), 's', r_pi) )

        return self.potential_vector


    def calculate_interaction_matrix(self):

        interaction_matrix = np.zeros ((self.ndof,self.ndof))

        for p in range(self.ndof):

            for q in range(self.ndof):

                if self.gas_model.atom(p) != self.gas_model.atom(q):

                    r_pq = self.atomic_coordinates[self.gas_model.atom(p)] - self.atomic_coordinates[self.gas_model.atom(q)]

                    interaction_matrix[p,q] = self.coulomb_energy(self.gas_model.orb(p),self.gas_model.orb(q), r_pq)

                if p==q and self.gas_model.orb(p)=='s':

                    interaction_matrix[p,q] = self.gas_model.model_parameters['coulomb_s']

                if p==q and self.gas_model.orb(p) in self.gas_model.p_orbitals:

                    interaction_matrix[p,q] = self.gas_model.model_parameters['coulomb_p']

        return interaction_matrix


    def chi_on_atom(self, o1, o2, o3):

        if o1 == o2 and o3 =='s':

            return 1.0

        if o1 == o3 and o3 in self.gas_model.p_orbitals and o2 =='s':

            return self.gas_model.model_parameters['dipole']

        if o2 == o3 and o3 in self.gas_model.p_orbitals and o1 =='s':

            return self.gas_model.model_parameters['dipole']

        return 0.0


    def calculate_chi_tensor(self):

        chi_tensor = np.zeros( (self.ndof, self.ndof, self.ndof) )

        for p in range(self.ndof):

            for orb_q in self.gas_model.orbital_types:

                q = self.gas_model.ao_index(self.gas_model.atom(p), orb_q)

                for orb_r in self.gas_model.orbital_types:

                    r = self.gas_model.ao_index(self.gas_model.atom(p), orb_r)

                    chi_tensor[p,q,r] = self.chi_on_atom(self.gas_model.orb(p), self.gas_model.orb(q), self.gas_model.orb(r))

        return chi_tensor


    def calculate_hamiltonian_matrix(self):

        hamiltonian_matrix = np.zeros( (self.ndof, self.ndof) )

        potential_vector = self.calculate_potential_vector()

        for p in range(self.ndof):

            for q in range(self.ndof):

                if self.gas_model.atom(p) != self.gas_model.atom(q):

                    r_pq = self.atomic_coordinates[self.gas_model.atom(p)] - self.atomic_coordinates[self.gas_model.atom(q)]

                    hamiltonian_matrix[p,q] = self.hopping_energy(self.gas_model.orb(p), self.gas_model.orb(q), r_pq)

                if self.gas_model.atom(p) == self.gas_model.atom(q):

                    if p == q and self.gas_model.orb(p) == 's':

                        hamiltonian_matrix[p,q] += self.gas_model.model_parameters['energy_s']

                    if p == q and self.gas_model.orb(p) in self.gas_model.p_orbitals:

                        hamiltonian_matrix[p,q] += self.gas_model.model_parameters['energy_p']

                    for orb_r in self.gas_model.orbital_types:

                        r = self.gas_model.ao_index(self.gas_model.atom(p), orb_r)

                        hamiltonian_matrix[p,q] += ( self.chi_on_atom(self.gas_model.orb(p), self.gas_model.orb(q), orb_r)
                                                 * self.potential_vector[r] )

        return hamiltonian_matrix


    def calculate_atomic_density_matrix(self):

        density_matrix = np.zeros( (self.ndof, self.ndof) )

        for p in range(self.ndof):

            density_matrix[p,p] = self.gas_model.orbital_occupation[self.gas_model.orb(p)]

        return density_matrix


    def calculate_fock_matrix(self, old_density_matrix):

        fock_matrix = self.hamiltonian_matrix.copy()

        fock_matrix += 2.0*np.einsum('pqt,rsu,tu,rs->pq', self.chi_tensor, self.chi_tensor, self.interaction_matrix, old_density_matrix , optimize=True)

        fock_matrix -= np.einsum('rqt,psu,tu,rs->pq', self.chi_tensor, self.chi_tensor, self.interaction_matrix, old_density_matrix, optimize=True)

        return fock_matrix


    def calculate_density_matrix(self):

        num_occ = (self.gas_model.ionic_charge//2) * np.size(self.fock_matrix,0) // self.gas_model.orbitals_per_atom

        orbital_energy, orbital_matrix = np.linalg.eigh(self.fock_matrix)

        occupied_matrix = orbital_matrix[:,:num_occ]

        density_matrix = occupied_matrix @ occupied_matrix.T

        return density_matrix


    def scf_cycle( self, max_scf_iterations = 100, mixing_fraction = 0.25, convergence_tolerance = 1e-10):

        self.density_matrix = self.calculate_density_matrix()

        old_density_matrix = self.density_matrix.copy()

        for iteration in range(max_scf_iterations):

            self.fock_matrix = self.calculate_fock_matrix(old_density_matrix)

            self.density_matrix = self.calculate_density_matrix()

            error_norm = np.linalg.norm( old_density_matrix - self.density_matrix)

            print(iteration, error_norm)

            if error_norm < convergence_tolerance:

                return self.density_matrix, self.fock_matrix

            old_density_matrix = (mixing_fraction * self.density_matrix + (1-mixing_fraction) * old_density_matrix )

        print("Warning: SCF Cycle did not converge")

        return self.density_matrix, self.fock_matrix


    def calculate_energy_scf(self):

        energy_scf = np.einsum('pq,pq', self.hamiltonian_matrix + self.fock_matrix, self.density_matrix)

        return energy_scf



argon = Noble_Gas_Model('Argon')
print(argon.model_parameters)
print(argon.ionic_charge)
print(argon.orbital_types)
print(argon.orbitals_per_atom)
print(argon.p_orbitals)
print(argon.vec)
print(argon.orbital_occupation)
print(argon.atom(5))
print(argon.orb(5))
print(argon.ao_index(argon.atom(5),argon.orb(5)))

atomic_coordinates = np.array([[0.0,0.0,0.0], [3.0,4.0,5.0]])

hf1 = HartreeFock(atomic_coordinates, argon)
hf1.scf_cycle()
print(hf1.density_matrix)
print(hf1.calculate_energy_ion() + hf1.calculate_energy_scf())
