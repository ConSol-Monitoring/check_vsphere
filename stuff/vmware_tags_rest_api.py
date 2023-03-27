from requests import Session
from typing import List, Dict

VALUE_KEY = 'value'


class VMTagReader:
    def __init__(self, vcenter_url: str, login: str, password: str):
        self.host = vcenter_url
        self.session = Session()
        self.session.auth = (login, password)

    def read_vms_tags(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Read categories and theirs tags associated with VM

        :return: Dict{vm_id: Dict{category:tag_list}}
        """

        self.__connect()
        cat_ids = self.__read_categories_ids()
        cat_infos = self.__read_categories_info(cat_ids)
        tag_assoc = self.__read_tags_assoc()
        return self.__read_tags_category(cat_infos, tag_assoc)

    def __connect(self) -> None:
        # curl -X POST https://my-company-vcenter.com/rest/com/vmware/cis/session -u my_login:my_pass
        res = self.session.post(f'{self.host}/rest/com/vmware/cis/session')
        self.session.headers.update({'vmware-api-session-id': res.json()[VALUE_KEY]})

    def __read_categories_ids(self) -> List[str]:
        # curl -X GET 'https://my-company-vcenter.com/rest/com/vmware/cis/tagging/category' -H "vmware-api-session-id:32e4cxxxxxxxx99a300a64312xxxx2f5"
        res = self.session.get(f'{self.host}/rest/com/vmware/cis/tagging/category')
        return res.json()[VALUE_KEY]

    def __read_categories_info(self, cat_ids: List[str]) -> Dict[str, Dict]:
        # curl -X GET 'https://my-company-vcenter.com/rest/com/vmware/cis/tagging/category/id:urn:vmomi:InventoryServiceCategory:90xxxx9d-4xxd-4xx0-8xxx8-02804xxxx57f:GLOBAL' -H "vmware-api-session-id:{id}"
        cat_infos: Dict[str, Dict] = {}
        for ci in cat_ids:
            res = self.session.get(f'{self.host}/rest/com/vmware/cis/tagging/category/id:{ci}')
            cat_infos[ci] = res.json()[VALUE_KEY]
        return cat_infos

    def __read_tags_assoc(self) -> Dict[str, List[str]]:
        # curl -X GET https://my-company-vcenter.com/api/vcenter/tagging/associations -H "vmware-api-session-id:{id}"
        res = self.session.get(f'{self.host}/api/vcenter/tagging/associations')
        tag_assoc: Dict[str, List[str]] = {}
        for a in res.json()['associations']:
            obj = a['object']
            if obj['type'] == 'VirtualMachine':
                vm_id = obj['id']
                if vm_id not in tag_assoc:
                    tag_assoc[vm_id] = []
                tag_assoc[vm_id].append(a['tag'])

        return tag_assoc

    def __read_tags_category(self, cat_infos: Dict[str, str], tag_assoc: Dict[str, List[str]]) -> Dict[str, Dict[str, List[str]]]:
        # curl -X GET 'https://my-company-vcenter.com/rest/com/vmware/cis/tagging/tag/id:urn:vmomi:InventoryServiceTag:01xx0e6b-fxxc-4xx5-a086-3220xxa1e917:GLOBAL' -H "vmware-api-session-id:{id}"
        vm_cat_tags: Dict[str, Dict[str, List[str]]] = {}
        for vi, tags in tag_assoc.items():
            for t in tags:
                res = self.session.get(f'{self.host}/rest/com/vmware/cis/tagging/tag/id:{t}')
                ci = res.json()[VALUE_KEY]['category_id']
                cat_name = cat_infos[ci]['name']
                tag_name = res.json()[VALUE_KEY]['name']
                if vi not in vm_cat_tags:
                    vm_cat_tags[vi] = {}
                if cat_name not in vm_cat_tags[vi]:
                    vm_cat_tags[vi][cat_name] = []
                vm_cat_tags[vi][cat_name].append(tag_name)
        return vm_cat_tags


if __name__ == "__main__":
    vmr = VMTagReader(
        vcenter_host='https://my-company-vcenter.com',
        login='my_login',
        password='my_password')
    vm_tags = vmr.read_vms_tags()
    print(vm_tags)
