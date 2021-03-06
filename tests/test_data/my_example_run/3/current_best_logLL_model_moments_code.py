import moments
import numpy as np

def model_func(params, ns):
	t1, nu11, s1, t2, nu21, nu22, m2_12, m2_21 = params
	sts = moments.LinearSystem_1D.steady_state_1D(np.sum(ns))
	fs = moments.Spectrum(sts)
	nu1_func = lambda t: 1.0 + (nu11 - 1.0) * (t / t1)
	fs.integrate(tf=t1, Npop=lambda t: [nu1_func(t)], dt_fac=0.01)
	fs = moments.Manips.split_1D_to_2D(fs, ns[0], ns[1])
	nu2_func = lambda t: ((1 - s1) * nu11) + (nu22 - ((1 - s1) * nu11)) * (t / t2)
	migs = np.array([[0, m2_12], [m2_21, 0]])
	fs.integrate(tf=t2, Npop=lambda t: [nu21, nu2_func(t)], m=migs, dt_fac=0.01)
	return fs

data = moments.Spectrum.from_file('/home/katenos/Workspace/popgen/GADMA/fs_examples/YRI_CEU.fs')
ns = data.sample_sizes

p0 = [0.4998572004354712, 2.357114661127308, 0.9984806062829666, 0.09461000843655785, 1.7425719794077874, 1.2368394548443258, 0.9299543753642668, 0.8621179886837054]
model = model_func(p0, ns)
ll_model = moments.Inference.ll_multinom(model, data)
print('Model log likelihood (LL(model, data)): {0}'.format(ll_model))

theta = moments.Inference.optimal_sfs_scaling(model, data)
print('Optimal value of theta: {0}'.format(theta))
theta0 = 0.37976
Nanc = int(theta / theta0)
print('Size of ancestral population: {0}'.format(Nanc))
