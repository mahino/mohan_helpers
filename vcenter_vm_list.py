
import ssl
from pyVmomi import vim, vmodl
from pyVim import connect

"""
VCENTER_USERNAME = "user"
VCENTER_PASSWORD = "pass"
VCENTER_IP = "10.41.26.208"
VM_PORT = 6000
VCENTER_DATACENTER = "DC0"
"""
VCENTER_USERNAME = "administrator@vsphere.local"
VCENTER_PASSWORD = "Nutanix/4u"
#VCENTER_IP = "10.46.1.213"
VCENTER_IP = "10.46.1.215"
VM_PORT = 443
VCENTER_DATACENTER = "systest_calm_vcenter"
#VCENTER_DATACENTER = "Auto_systest_calm_vcenter-DC"

class VCenterHelper(object):
  """
  This Class is used to perform some operations on vcenter
  """

  def __init__(self, user_spawned):
    """
    init method to initialize connetion with vcenter
    Args:
      user_spawned(str): name of the usetr spawned
    Raises:
      Exceptions
    """
    try:
      sslcontext = ssl._create_unverified_context()
      self.si = connect.SmartConnect(host=VCENTER_IP,
                                     user=VCENTER_USERNAME,
                                     pwd=VCENTER_PASSWORD,
                                     port=VM_PORT, sslContext=sslcontext)
      if not self.si:
        raise Exception("Could not connect to the specified host using [{0}] \
                        and [{1}]".format(VCENTER_USERNAME, VCENTER_PASSWORD))
    except vim.fault.InvalidLogin as ex:
      print(user_spawned, "Unable to connect to vmware server: %s" % ex)
      raise Exception(
        "Unable to connect to vmware server: '{0}' "
        "with creds provided: '{1}'".format(VCENTER_IP, ex.msg))

    except Exception as ex:
      print(user_spawned, "Unable to connect to vmware server: %s" % ex)
      raise Exception(
        "Unable to connect to vmware server: '{0}'".format(VCENTER_IP))

  @classmethod
  def get_container_view(cls, service_instance, obj_type, container=None):
    """
    Get a vSphere Container View reference to all objects of type 'obj_type'
    It is up to the caller to take care of destroying the View when no longer
    needed.

    Args:
      service_instance(vim.ServiceInstance): root object
      for invenory traversal
      obj_type(list): A list of managed object types
      container(vim.ManagedEntity): The object that the view presents
    Returns:
      (vim.view.ContainerView): A container view ref to the discovered
      managed objects
    """
    if not container:
      container = service_instance.content.rootFolder

    view_ref = service_instance.content.viewManager.CreateContainerView(
      container=container,
      type=obj_type,
      recursive=True
    )
    return view_ref

  @classmethod
  def collect_properties(cls, service_instance, view_ref,
                         obj_type, path_set=None, include_mors=False):
    """
    Collect properties
    for managed objects from a view ref
    Check the vSphere API documentation
    for example on retrieving
    object properties:
      -http: //goo.gl/erbFDz
    Args:
      service_instance(vim.ServiceInstance): ServiceInstance connection
      view_ref(vim.view.*): Starting point of inventory navigation
      obj_type(vim.*): Type of managed object
      path_set(list): List of properties to retrieve
      include_mors(bool): If True include the managed objects
      refs in the result
    Returns:
      A list of properties
      for the managed objects
    """
    collector = service_instance.content.propertyCollector

    # Create object specification to define the starting point of
    # inventory navigation
    obj_spec = vmodl.query.PropertyCollector.ObjectSpec()
    obj_spec.obj = view_ref
    obj_spec.skip = True

    # Create a traversal specification to identify the path for collection
    traversal_spec = vmodl.query.PropertyCollector.TraversalSpec()
    traversal_spec.name = 'traverseEntities'
    traversal_spec.path = 'view'
    traversal_spec.skip = False
    traversal_spec.type = view_ref.__class__
    obj_spec.selectSet = [traversal_spec]

    # Identify the properties to the retrieved
    property_spec = vmodl.query.PropertyCollector.PropertySpec()
    property_spec.type = obj_type

    if not path_set:
      property_spec.all = True

    property_spec.pathSet = path_set

    # Add the object and property specification to the# property filter
    # specification
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = [obj_spec]
    filter_spec.propSet = [property_spec]

    # Retrieve properties
    props = collector.RetrieveContents([filter_spec])

    data = []
    for obj in props:
      properties = {}
      for prop in obj.propSet:
        properties[prop.name] = prop.val

      if include_mors:
        properties['obj'] = obj.obj

      data.append(properties)
    return data

  @classmethod
  def wait_for_tasks(cls, **kwargs):
    """
    Given the service instance si and tasks, it returns after all the
    tasks are complete
    Args:
      kwargs:
        service_instance(vim.ServiceInstance): root object
          for vcenter
        inventory traversal
        tasks(vim.Task): (create / update / delete etc) tasks to wait
          for completion
        user_spawned(str): name of the user spawned
    Returns:
      Raises:
    """
    service_instance = kwargs.get('service_instance')
    tasks = kwargs.get('tasks')
    user_spawned = kwargs.get('user_spawned')

    property_collector = service_instance.content.propertyCollector
    task_list = [str(task) for task in tasks]

    # Create filter
    obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                 for task in tasks]
    property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                               pathSet=[],
                                                               all=True)
    filter_spec = vmodl.query.PropertyCollector.FilterSpec()
    filter_spec.objectSet = obj_specs
    filter_spec.propSet = [property_spec]
    pcfilter = property_collector.CreateFilter(filter_spec, True)
    try:
      version, state = None, None

      # Loop looking for updates till the state moves to a completed state.
      while len(task_list):
        update = property_collector.WaitForUpdates(version)
        for filter_set in update.filterSet:
          for obj_set in filter_set.objectSet:
            task = obj_set.obj
            for change in obj_set.changeSet:
              if change.name == 'info':
                state = change.val.state
              elif change.name == 'info.state':
                state = change.val
              else:
                continue
              if state == vim.TaskInfo.State.success:

                #Remove task from taskList
                task_list.remove(str(task))
              elif state == vim.TaskInfo.State.error:
                print(user_spawned, task.info.error.msg)
                raise task.info.error

        # Move to next version
        version = update.version
    finally:
      if pcfilter:
        pcfilter.Destroy()

  def get_objects_by_prop(self, service_instance, prop, obj_type,
                          obj_value, container=None):
    """
    Get the vSphere object with the specified property
    Args:
      service_instance(vim.ServiceInstance): root object
        for invenory traversal
      prop(str): name of the property
      obj_type(str): type of a managed object
      obj_value(str): value of a managed object that needs to be matched
      container(vim.ManagedEntity): The object that the view presents
    Returns:
      (vim.ManagedEntity);
      First Object that match the value
    """

    view = self.get_container_view(service_instance, obj_type=[obj_type],
                                   container=container)
    props = [prop]
    obj_details = self.collect_properties(service_instance, view_ref=view,
                                          obj_type=obj_type, path_set=props,
                                          include_mors=True)

    # print number of datacenters
    #print(len(obj_details))
    try:
      obj = [ob.pop('obj') for ob in obj_details if ob.get(prop) ==
             obj_value][0]
    except IndexError:
      raise Exception("Failed to fetch VMware object: '{0}' with {1}: '{2}'" \
        .format(obj_type.__name__, prop, obj_value))

    return obj

  def get_datacenter(self, dc_name, user_spawned):
    """
    Returns datacenter object given the datacenter name
    Args:
      dc_name(str): datacenter name
      user_spawned(str): name of the user spawned
    Returns:
      (vim.Datacenter) datacenter object
    Raises:
    """
    try:
      datacenter = None
      if dc_name:
        datacenter = self.get_objects_by_prop(self.si, prop='name',
                                              obj_type=vim.Datacenter,
                                              obj_value=dc_name)
      return datacenter
    except Exception as ex:
      print(user_spawned, "VMware get datacenter failed: %s" % ex)
      raise

  def get_vm_in_dc(self, datacenter_name, vm_id, user_spawned):
    """
    Get vm in a given datacenter
    Args:
      datacenter_name(str): datacenter name
      vm_id(str): unique id of the esx vm
      user_spawned(str): name of the user spawned
    Returns:
      (vim.VirtualMachine)
    Raises:
    """
    datacenter = self.get_datacenter(datacenter_name, user_spawned)
    if not datacenter:
      raise Exception("Datacenter with name: '{0}' not found".format(
        datacenter_name))
    vm = self.si.content.searchIndex.FindByUuid(datacenter, vm_id, True, True)
    if not vm:
      raise Exception('VM with id: {0} not found'.format(
        vm_id))
    return vm

  def vm_power_actions(self, power_action, vm, user_spawned):
    """
    Do power off operation on VM
    Args:
      vm(obj): vm object
      power_action(str): power action on vm ON or OFF.
      user_spawned(str): name of the user spawned
    Returns: status of operation
    """
    try:
      if power_action == "ON":
        task = vm.PowerOnVM_Task()
      elif power_action == "OFF":
        task = vm.PowerOffVM_Task()
      self.wait_for_tasks(service_instance=self.si, tasks=[task],
                          user_spawned=user_spawned)
      print(user_spawned, "Successfully powered [{0}] the" \
             " VM [{1}]".format(power_action, vm))
      return True
    except Exception as ex:
      print(user_spawned, "Exception occured while switching [{1}] the" \
             " VM [{2}] : [{0}]".format(ex.message, power_action, vm))
      return False

  def reconfigure_vm(self, **kwargs):
    """
    Do reconfig operation on vm
    Args:
      kwargs:
        datacenter_name(str): name of the datacenter
        vm_ids_list(list): vm ids list
        numCPUs(int): num of cpus
        memoryMB(int): memory in MB
        user_spawned(str): name of the user spawned

    """
    datacenter_name = kwargs.get('datacenter_name', VCENTER_DATACENTER)
    vm_ids_list = kwargs.get('vm_ids_list')
    numCPUs = kwargs.get('numCPUs')
    memoryMB = kwargs.get('memoryMB')
    user_spawned = kwargs.get('user_spawned')

    spec = vim.vm.ConfigSpec()
    spec.numCPUs = numCPUs
    spec.memoryMB = memoryMB

    list_of_vm_objects = []
    for vm_id in vm_ids_list:
      vm = self.get_vm_in_dc(datacenter_name, vm_id, user_spawned)
      # Vm power off for reconfigure
      power_action = self.vm_power_actions("OFF", vm, user_spawned)
      if power_action:
        list_of_vm_objects.append(vm)

    reconfigure_tasks = []
    for vm_id in vm_ids_list:
      vm = self.get_vm_in_dc(datacenter_name, vm_id, user_spawned)
      try:
        task = vm.Reconfigure(spec)
        reconfigure_tasks.append(task)
      except Exception as ex:
        print(user_spawned, "WARNING: Exception occured while reconfiguring" \
               " the VM: {}".format(ex.message))

    self.wait_for_tasks(service_instance=self.si, tasks=reconfigure_tasks,
                        user_spawned=user_spawned)
    print(user_spawned, "Reconfigured the all VM successfully in vcenter")

    for vm in list_of_vm_objects:
      self.vm_power_actions("ON", vm, user_spawned)

  def delete_all_vms(self, **kwargs):
    """
    This method deltes all vms with name pattern
    Args:
      kwargs:
        name_pattern(str): name pattern
    Returns:
      None
    """
    name_pattern = kwargs.get('name_pattern', 'vmw_ins_del')
    datacenter_name = kwargs.get('datacenter_name', VCENTER_DATACENTER) 

    dc = self.get_datacenter(datacenter_name, 'mohan')
    vmfolder = dc.vmFolder
    vmlist = vmfolder.childEntity
    for vm in vmlist:
      if name_pattern in vm.name:
        print("deleting vm [{}]".format(vm.name))
        self.vm_power_actions("OFF", vm, 'mohan')
        vm.Destroy_Task()

  def list_all_vms(self, **kwargs):
    """
    This method list all vms 
    Args:
    Returns:
      None
    """
    #al_acc = ['Auto_cluster_prod_prakash_ks_4f4549e3012d-DC', '10.46.201.84-DC', 'Auto_cluster_prod_svc.qms.global-pool_f3207fd38b1f-DC', 'Auto_systest_calm_vcenter-DC', 'Auto_mixed_cluster_metro-DC', 'XiNetworking-VPN-NishanthPrabhu', 'Carrot-1-DC', 'Auto_esx_angel_sandbox-DC', 'auto_cluster_prod_Sundarakumar_4f0ba4215360-DC', 'Luigi10-DC', 'Auto_cluster_prod_sujesh_puthanveedu_4f79ab35b9da-DC', 'Goodyear-c1-DC', 'Auto_smoke_remote-DC', 'Auto_cluster_prod_abhishek_agrawal1_1ab5f1b6bb73-DC', 'Auto_cluster_prod_noufal_muhammed_1a654d486db9-DC', 'Sherlock-DC', 'Auto_mixed_cluster_remote-DC', 'Auto_cluster_prod_amogh_mavinagidad_f383faa4f9e9-DC', 'Auto_auto_smoke_source-DC', 'Auto_cluster_prod_pingjin_wen_4f28e41ddf7a-DC', 'Auto_cluster_qms_prakash_ks_f39c966e454e-DC', 'magneto-DC', 'Auto_cluster_prod_amogh_mavinagidad_1a106aedd8d8-DC', 'New_cluster-DC', 'sabine36-4', 'auto_cluster_prod_karthik_subramaniam_f31d0ae51db3-DC', 'Auto_cluster_prod_saurabh_goyal_f3a239dc37de-DC', 'Auto_cluster_prod_svc.qms.global-pool_4f3a12d2115b-DC', 'Auto_cluster_prod_amogh_mavinagidad_f398d293f7ee-DC', 'Auto_cluster_prod_amogh_mavinagidad_f383faa4f9ed-DC', 'Auto_cluster_prod_svc.qms.global-pool_f320700913ad-DC', 'Auto_cluster_prod_noufal_muhammed_f35e4a0c389b-DC', 'New_cluster_mixed-DC', 'Systest-vcenter-DC', 'Naruto-DC', 'auto_cluster_smoke_cdp_dr-DC', 'Auto_cluster_prod_amogh_mavinagidad_f398d293f7ea-DC', 'Auto_cluster_prod_saurabh_goyal_4fbb9431e476-DC', 'Daredevil03-c3-DC', 'Daredevil01-c4-DC', 'Auto_cluster_prod_amogh_mavinagidad_1a106aedd8d4-DC', 'Auto_cluster_prod_jita_616d11e88e79cee394e1d2c1_1a106f1360e1-DC', 'Auto_cluster_prod_aasheesh_tandon1_4fd2e1d4ea6b-DC', 'Auto_cluster_prod_aasheesh_tandon1_4fd2f6786030-DC', 'Auto_cluster_prod_ashish_kale_4f39fd886fd5-DC', 'Auto_cluster_prod_svc.qms.global-pool_4f3a0923b0c7-DC', 'Auto_cluster_prod_svc.qms.global-pool_f3207ee37bff-DC', 'Auto_cluster_prod_svc.qms.global-pool_f320843120c9-DC', 'Auto_cluster_prod_svc.qms.global-pool_1a106528488f-DC']
    al_acc = [VCENTER_DATACENTER]
    s=0
    for i in al_acc:
      dc = self.get_datacenter(i, 'mohan')
      vms_count = len(dc.vmFolder.childEntity)
      print(i, vms_count)
      s+= vms_count
    print(len(al_acc), s)

s=VCenterHelper('mohan')
s.list_all_vms()

